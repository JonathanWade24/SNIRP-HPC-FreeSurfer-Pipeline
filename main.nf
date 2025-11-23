#!/usr/bin/env nextflow

nextflow.enable.dsl=2

/*
 * Comprehensive Neuroimaging Pipeline for HPC/Slurm
 * Stages: DICOM→BIDS, Validation, MRIQC, FastSurfer (cross-sectional & longitudinal),
 *         Atlas extraction, Stats aggregation, Summary generation
 */

// ================================================================================
// PARAMETERS
// ================================================================================

params.help = false

if (params.help) {
    log.info """
    ====================================
    Neuroimaging Pipeline - Usage
    ====================================
    
    Required Parameters:
      --input_mode          Input type: 'dicom', 'bids', or 'nii' (default: 'nii')
      
    Optional Parameters:
      --run_dicom_conversion    Convert DICOM to BIDS (default: false)
      --run_bids_validation     Validate BIDS structure (default: true)
      --run_mriqc              Run MRIQC quality control (default: false)
      --run_longitudinal       Process longitudinal data (default: false)
      
      --dicom_dir              DICOM input directory (default: \${projectDir}/dicom)
      --bids_dir               BIDS directory (default: \${projectDir}/bids)
      --nii_dir                NIfTI directory (default: \${projectDir}/nii)
      --output_dir             FastSurfer output (default: \${projectDir}/fs_outputs)
      --long_output_dir        Longitudinal output (default: \${projectDir}/long_outputs)
      --qc_dir                 QC output (default: \${projectDir}/qc)
      --stats_dir              Stats output (default: \${projectDir}/stats)
      
      --extract_schaefer       Extract Schaefer atlas (default: true)
      --extract_glasser        Extract Glasser atlas (default: true)
      --extract_yeo            Extract Yeo networks (default: true)
      --schaefer_parcels       Schaefer parcel counts (default: "100,200,400")
      
      --threads                CPU threads per job (default: 8)
      
    Examples:
      # Basic cross-sectional from NIfTI
      nextflow run main.nf -profile slurm
      
      # Full pipeline from DICOM with MRIQC
      nextflow run main.nf -profile slurm --input_mode dicom --run_dicom_conversion --run_mriqc
      
      # Longitudinal processing
      nextflow run main.nf -profile slurm --input_mode bids --run_longitudinal
    ====================================
    """.stripIndent()
    exit 0
}

// Print pipeline information
log.info """\
    ====================================
    Neuroimaging Pipeline
    ====================================
    Input mode         : ${params.input_mode}
    DICOM conversion   : ${params.run_dicom_conversion}
    BIDS validation    : ${params.run_bids_validation}
    MRIQC              : ${params.run_mriqc}
    Longitudinal       : ${params.run_longitudinal}
    Output directory   : ${params.output_dir}
    Threads per job    : ${params.threads}
    ====================================
    """
    .stripIndent()

// ================================================================================
// PROCESS DEFINITIONS
// ================================================================================

/*
 * Process: Convert DICOM to BIDS using HeuDiConv
 */
process DICOM_TO_BIDS {
    tag "${subject_id}"
    
    publishDir "${params.bids_dir}", mode: 'copy', overwrite: false
    
    container params.heudiconv_container
    
    input:
    tuple val(subject_id), path(dicom_dir)
    
    output:
    tuple val(subject_id), path("sub-${subject_id}"), emit: bids_subject
    path ".heudiconv/${subject_id}/info", emit: heuristic_info, optional: true
    
    script:
    """
    # Create output directory
    mkdir -p sub-${subject_id}
    
    # Run HeuDiConv conversion
    heudiconv \
        -d ${dicom_dir}/*/*.dcm \
        -o . \
        -f ${projectDir}/bin/heuristic.py \
        -s ${subject_id} \
        -c dcm2niix \
        -b \
        --overwrite
    
    echo "DICOM to BIDS conversion completed for ${subject_id}"
    """
}

/*
 * Process: Validate BIDS structure
 */
process BIDS_VALIDATE {
    tag "BIDS validation"
    
    publishDir "${params.bids_dir}", mode: 'copy'
    
    container params.bids_validator_container
    
    input:
    path bids_dir
    
    output:
    path "bids_validation_report.txt", emit: report
    
    script:
    """
    # Run BIDS validator
    bids-validator ${bids_dir} --json > validation.json || true
    
    # Create readable report
    if [ -f validation.json ]; then
        echo "BIDS Validation Report" > bids_validation_report.txt
        echo "======================" >> bids_validation_report.txt
        echo "" >> bids_validation_report.txt
        cat validation.json >> bids_validation_report.txt
    else
        echo "BIDS validation completed successfully" > bids_validation_report.txt
    fi
    """
}

/*
 * Process: Run MRIQC for quality control
 */
process MRIQC {
    tag "${subject_id}"
    
    publishDir "${params.qc_dir}/mriqc", mode: 'copy'
    
    container params.mriqc_container
    
    input:
    tuple val(subject_id), path(bids_subject)
    path bids_root
    
    output:
    tuple val(subject_id), path("sub-${subject_id}"), emit: qc_subject
    path "sub-${subject_id}/*.html", emit: reports, optional: true
    path "sub-${subject_id}/*.json", emit: metrics, optional: true
    
    script:
    """
    mkdir -p sub-${subject_id}
    
    # Run MRIQC for this subject
    mriqc ${bids_root} sub-${subject_id} \
        participant \
        --participant-label ${subject_id} \
        --no-sub \
        -w work_mriqc \
        --n_procs ${task.cpus} \
        --mem_gb ${task.memory.toGiga()} \
        --float32 \
        --ants-nthreads ${task.cpus}
    
    echo "MRIQC completed for ${subject_id}"
    """
}

/*
 * Process: MRIQC Group Report
 */
process MRIQC_GROUP {
    tag "MRIQC group report"
    
    publishDir "${params.qc_dir}/mriqc", mode: 'copy'
    
    container params.mriqc_container
    
    input:
    path bids_root
    path "derivatives/mriqc/*"
    
    output:
    path "group_*.html", emit: group_reports
    path "group_*.tsv", emit: group_metrics
    
    script:
    """
    # Run MRIQC group level
    mriqc ${bids_root} . \
        group \
        -w work_mriqc_group \
        --n_procs ${task.cpus}
    
    echo "MRIQC group report completed"
    """
}

/*
 * Process: FastSurfer Cross-sectional Reconstruction
 */
process FASTSURFER_CROSS {
    tag "${subject_id}"
    
    publishDir "${params.output_dir}", mode: 'copy', overwrite: false
    
    input:
    tuple val(subject_id), path(t1_image)
    
    output:
    tuple val(subject_id), path("${subject_id}"), emit: subject_dir
    path "${subject_id}/scripts/recon-surf.log", optional: true, emit: log
    
    script:
    """
    # Create output directory
    mkdir -p ${subject_id}

    # Get absolute path to T1 image
    T1_ABS=\$(readlink -f ${t1_image})

    # Run FastSurfer in CPU mode
    /fastsurfer/run_fastsurfer.sh \
        --t1 \${T1_ABS} \
        --sid ${subject_id} \
        --sd \${PWD} \
        --fs_license ${params.license} \
        --threads ${params.threads} \
        --py python

    echo "FastSurfer cross-sectional processing completed for ${subject_id}"
    """
}

/*
 * Process: FastSurfer Longitudinal Base (Template Creation)
 */
process FASTSURFER_LONG_BASE {
    tag "${base_id}"
    
    publishDir "${params.long_output_dir}", mode: 'copy', overwrite: false
    
    input:
    tuple val(base_id), val(timepoint_ids), path(timepoint_dirs)
    
    output:
    tuple val(base_id), path("${base_id}"), emit: base_dir
    path "${base_id}/scripts/recon-all-base.log", optional: true, emit: log
    
    script:
    def tp_flags = timepoint_ids.collect { "-tp ${it}" }.join(' ')
    """
    # Load FreeSurfer module
    module load neurocontainers
    module load freesurfer

    # Set FreeSurfer license
    export FS_LICENSE=${params.license}

    # Timepoint directories are already staged by Nextflow
    # Just verify they exist
    ${timepoint_ids.collect { "ls -d ${it} > /dev/null" }.join('\n    ')}

    # Run longitudinal base creation
    recon-all \
        -base ${base_id} \
        ${tp_flags} \
        -all \
        -sd . \
        -parallel \
        -openmp ${params.threads}

    echo "Longitudinal base template created for ${base_id}"
    """
}

/*
 * Process: FastSurfer Longitudinal Timepoint Processing
 */
process FASTSURFER_LONG_TP {
    tag "${timepoint_id}_long"
    
    publishDir "${params.long_output_dir}", mode: 'copy', overwrite: false
    
    input:
    tuple val(base_id), val(timepoint_id), path(timepoint_dir), path(base_dir)
    
    output:
    tuple val(base_id), val(timepoint_id), path("${timepoint_id}.long.${base_id}"), emit: long_dir
    path "${timepoint_id}.long.${base_id}/scripts/recon-all.log", optional: true, emit: log
    
    script:
    """
    # Load FreeSurfer module
    module load neurocontainers
    module load freesurfer

    # Set FreeSurfer license
    export FS_LICENSE=${params.license}

    # Directories are already staged by Nextflow
    # Just verify they exist
    ls -d ${timepoint_id} > /dev/null
    ls -d ${base_id} > /dev/null

    # Run longitudinal timepoint processing
    recon-all \
        -long ${timepoint_id} ${base_id} \
        -all \
        -sd . \
        -parallel \
        -openmp ${params.threads}

    echo "Longitudinal processing completed for ${timepoint_id}"
    """
}

/*
 * Process: Extract Atlas Statistics
 */
process EXTRACT_ATLASES {
    tag "${subject_id}"
    
    publishDir "${params.stats_dir}/atlases", mode: 'copy'
    
    input:
    tuple val(subject_id), path(subject_dir)
    
    output:
    tuple val(subject_id), path("${subject_id}_atlases.json"), emit: atlas_json
    path "${subject_id}_atlases.csv", emit: atlas_csv
    
    script:
    """
    #!/usr/bin/env python3
    
    import sys
    sys.path.insert(0, '${projectDir}/bin')
    
    from extract_atlases import extract_all_atlases
    
    # Extract all atlas statistics
    extract_all_atlases(
        subject_dir='${subject_dir}',
        subject_id='${subject_id}',
        output_json='${subject_id}_atlases.json',
        output_csv='${subject_id}_atlases.csv',
        extract_schaefer=${params.extract_schaefer},
        extract_glasser=${params.extract_glasser},
        extract_yeo=${params.extract_yeo},
        extract_cobra=${params.extract_cobra},
        extract_neuromorphometrics=${params.extract_neuromorphometrics},
        schaefer_parcels='${params.schaefer_parcels}',
        atlas_dir='${projectDir}/bin/atlases'
    )
    
    print(f"Atlas extraction completed for ${subject_id}")
    """
}

/*
 * Process: Aggregate Statistics Across Subjects
 */
process AGGREGATE_STATS {
    tag "Aggregate statistics"
    
    publishDir "${params.stats_dir}", mode: 'copy'
    
    input:
    path "atlas_jsons/*"
    path "subject_dirs/*"
    
    output:
    path "cortical_thickness.csv", emit: thickness
    path "subcortical_volumes.csv", emit: volumes
    path "aparc_dkt.csv", emit: aparc_dkt
    path "qc_summary.csv", emit: qc_summary, optional: true
    
    script:
    """
    #!/usr/bin/env python3
    
    import sys
    sys.path.insert(0, '${projectDir}/bin')
    
    from aggregate_stats import aggregate_all_stats
    
    # Aggregate all statistics
    aggregate_all_stats(
        atlas_json_dir='atlas_jsons',
        subject_dirs='subject_dirs',
        output_dir='.',
        qc_dir='${params.qc_dir}'
    )
    
    print("Statistics aggregation completed")
    """
}

/*
 * Process: Calculate Longitudinal Statistics
 */
process LONGITUDINAL_STATS {
    tag "Longitudinal statistics"
    
    publishDir "${params.stats_dir}", mode: 'copy'
    
    input:
    path "long_dirs/*"
    
    output:
    path "longitudinal_slope_estimates.csv", emit: slopes
    path "longitudinal_percent_change.csv", emit: percent_change
    
    script:
    """
    #!/usr/bin/env python3
    
    import sys
    sys.path.insert(0, '${projectDir}/bin')
    
    from longitudinal_stats import calculate_longitudinal_stats
    
    # Calculate longitudinal statistics
    calculate_longitudinal_stats(
        long_dirs='long_dirs',
        output_slopes='longitudinal_slope_estimates.csv',
        output_percent='longitudinal_percent_change.csv'
    )
    
    print("Longitudinal statistics calculated")
    """
}

/*
 * Process: Aggregate QC Metrics
 */
process AGGREGATE_QC {
    tag "QC aggregation"
    
    publishDir "${params.stats_dir}", mode: 'copy'
    
    input:
    path "qc_jsons/*"
    
    output:
    path "qc_summary.csv", emit: qc_summary
    path "qc_outliers.txt", emit: outliers
    
    script:
    """
    #!/usr/bin/env python3
    
    import sys
    sys.path.insert(0, '${projectDir}/bin')
    
    from qc_aggregator import aggregate_qc_metrics
    
    # Aggregate QC metrics
    aggregate_qc_metrics(
        qc_json_dir='qc_jsons',
        output_csv='qc_summary.csv',
        output_outliers='qc_outliers.txt'
    )
    
    print("QC metrics aggregated")
    """
}

/*
 * Process: Generate Final Summary Report
 */
process GENERATE_SUMMARY {
    tag "Final summary"
    
    publishDir "${projectDir}", mode: 'copy'
    
    input:
    val subject_ids
    path thickness_csv, stageAs: 'thickness.csv'
    path volumes_csv, stageAs: 'volumes.csv'
    val pipeline_mode
    
    output:
    path "pipeline_summary.txt", emit: summary
    path "pipeline_summary.html", emit: html_summary
    
    script:
    def subjects = subject_ids.join('\n')
    def mode_desc = pipeline_mode == 'longitudinal' ? 'Longitudinal' : 'Cross-sectional'
    """
    # Generate text summary
    cat > pipeline_summary.txt <<EOF
    ====================================
    Neuroimaging Pipeline Summary
    ====================================
    
    Pipeline Mode: ${mode_desc}
    Processing completed on: \$(date)
    
    Total subjects processed: ${subject_ids.size()}
    
    Subjects:
    --------
${subjects}
    
    Output Directories:
    ------------------
    - FastSurfer outputs: ${params.output_dir}
    - Statistics: ${params.stats_dir}
    - QC reports: ${params.qc_dir}
    - Logs: ${projectDir}/logs
    
    Generated Files:
    ---------------
    - cortical_thickness.csv
    - subcortical_volumes.csv
    - aparc_dkt.csv
    ${pipeline_mode == 'longitudinal' ? '- longitudinal_slope_estimates.csv\n    - longitudinal_percent_change.csv' : ''}
    ${params.run_mriqc ? '- qc_summary.csv' : ''}
    
    ====================================
EOF
    
    # Generate HTML summary
    cat > pipeline_summary.html <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>Neuroimaging Pipeline Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; margin-top: 30px; }
        .info { background-color: #ecf0f1; padding: 15px; border-radius: 5px; }
        .subjects { background-color: #e8f8f5; padding: 15px; border-radius: 5px; }
        ul { line-height: 1.8; }
    </style>
</head>
<body>
    <h1>Neuroimaging Pipeline Summary</h1>
    
    <div class="info">
        <h2>Pipeline Information</h2>
        <ul>
            <li><strong>Mode:</strong> ${mode_desc}</li>
            <li><strong>Completed:</strong> \$(date)</li>
            <li><strong>Total Subjects:</strong> ${subject_ids.size()}</li>
        </ul>
    </div>
    
    <div class="subjects">
        <h2>Processed Subjects</h2>
        <ul>
${subject_ids.collect { "            <li>${it}</li>" }.join('\n')}
        </ul>
    </div>
    
    <h2>Output Directories</h2>
    <ul>
        <li><strong>FastSurfer outputs:</strong> ${params.output_dir}</li>
        <li><strong>Statistics:</strong> ${params.stats_dir}</li>
        <li><strong>QC reports:</strong> ${params.qc_dir}</li>
        <li><strong>Logs:</strong> ${projectDir}/logs</li>
    </ul>
    
    <h2>Generated Files</h2>
    <ul>
        <li>cortical_thickness.csv</li>
        <li>subcortical_volumes.csv</li>
        <li>aparc_dkt.csv</li>
        ${pipeline_mode == 'longitudinal' ? '<li>longitudinal_slope_estimates.csv</li>\n        <li>longitudinal_percent_change.csv</li>' : ''}
        ${params.run_mriqc ? '<li>qc_summary.csv</li>' : ''}
    </ul>
</body>
</html>
EOF
    
    echo "Summary report generated"
    """
}

// ================================================================================
// WORKFLOW DEFINITIONS
// ================================================================================

/*
 * Sub-workflow: DICOM to BIDS Conversion
 */
workflow DICOM_WORKFLOW {
    take:
    dicom_subjects
    
    main:
    // Convert DICOM to BIDS
    DICOM_TO_BIDS(dicom_subjects)
    
    // Validate BIDS structure if requested
    if (params.run_bids_validation) {
        BIDS_VALIDATE(params.bids_dir)
    }
    
    emit:
    bids_subjects = DICOM_TO_BIDS.out.bids_subject
}

/*
 * Sub-workflow: Quality Control with MRIQC
 */
workflow QC_WORKFLOW {
    take:
    bids_subjects
    
    main:
    // Run MRIQC on each subject
    MRIQC(bids_subjects, params.bids_dir)
    
    // Generate group report
    MRIQC_GROUP(
        params.bids_dir,
        MRIQC.out.metrics.collect()
    )
    
    // Aggregate QC metrics
    AGGREGATE_QC(MRIQC.out.metrics.collect())
    
    emit:
    qc_summary = AGGREGATE_QC.out.qc_summary
}

/*
 * Sub-workflow: Cross-sectional Processing
 */
workflow CROSS_SECTIONAL_WORKFLOW {
    take:
    t1_images
    
    main:
    // Run FastSurfer cross-sectional
    FASTSURFER_CROSS(t1_images)
    
    // Extract atlas statistics
    EXTRACT_ATLASES(FASTSURFER_CROSS.out.subject_dir)
    
    // Aggregate statistics
    AGGREGATE_STATS(
        EXTRACT_ATLASES.out.atlas_json.collect(),
        FASTSURFER_CROSS.out.subject_dir.collect()
    )
    
    emit:
    subject_dirs = FASTSURFER_CROSS.out.subject_dir
    thickness = AGGREGATE_STATS.out.thickness
    volumes = AGGREGATE_STATS.out.volumes
}

/*
 * Sub-workflow: Longitudinal Processing
 */
workflow LONGITUDINAL_WORKFLOW {
    take:
    t1_images
    
    main:
    // First run cross-sectional on all timepoints
    FASTSURFER_CROSS(t1_images)
    
    // Group timepoints by base subject
    timepoint_groups = FASTSURFER_CROSS.out.subject_dir
        .map { subject_id, dir ->
            // Extract base subject ID (remove session/timepoint suffix)
            def base_id = subject_id.replaceAll(/_(ses-\w+|tp\d+)$/, '')
            tuple(base_id, subject_id, dir)
        }
        .groupTuple()
    
    // Create longitudinal base templates
    FASTSURFER_LONG_BASE(
        timepoint_groups.map { base_id, tp_ids, tp_dirs ->
            tuple(base_id, tp_ids, tp_dirs)
        }
    )
    
    // Process each timepoint with its base
    long_inputs = timepoint_groups
        .combine(FASTSURFER_LONG_BASE.out.base_dir, by: 0)
        .flatMap { base_id, tp_ids, tp_dirs, base_dir ->
            tp_ids.withIndex().collect { tp_id, idx ->
                tuple(base_id, tp_id, tp_dirs[idx], base_dir)
            }
        }
    
    FASTSURFER_LONG_TP(long_inputs)
    
    // Calculate longitudinal statistics
    LONGITUDINAL_STATS(FASTSURFER_LONG_TP.out.long_dir.collect())
    
    emit:
    long_dirs = FASTSURFER_LONG_TP.out.long_dir
    slopes = LONGITUDINAL_STATS.out.slopes
    percent_change = LONGITUDINAL_STATS.out.percent_change
}

// ================================================================================
// MAIN WORKFLOW
// ================================================================================

workflow {
    // Initialize channels based on input mode
    if (params.input_mode == 'dicom' && params.run_dicom_conversion) {
        // DICOM input mode
        Channel
            .fromPath("${params.dicom_dir}/*", type: 'dir')
            .map { dir ->
                def subject_id = dir.name
                tuple(subject_id, dir)
            }
            .set { dicom_subjects_ch }
        
        // Convert DICOM to BIDS
        DICOM_WORKFLOW(dicom_subjects_ch)
        
        // Extract T1 images from BIDS
        Channel
            .fromPath("${params.bids_dir}/sub-*/ses-*/anat/*_T1w.nii.gz")
            .ifEmpty { error "No T1 images found in BIDS directory after conversion" }
            .map { file ->
                def subject_id = file.parent.parent.parent.name
                def session_id = file.parent.parent.name
                def full_id = "${subject_id}_${session_id}"
                tuple(full_id, file)
            }
            .set { t1_images_ch }
        
    } else if (params.input_mode == 'bids') {
        // BIDS input mode
        Channel
            .fromPath("${params.bids_dir}/sub-*/ses-*/anat/*_T1w.nii.gz")
            .ifEmpty { 
                // Try without session structure
                Channel.fromPath("${params.bids_dir}/sub-*/anat/*_T1w.nii.gz")
            }
            .map { file ->
                // Extract subject and session info
                def parts = file.toString().tokenize('/')
                def subject_idx = parts.findIndexOf { it.startsWith('sub-') }
                def subject_id = parts[subject_idx]
                
                // Check if there's a session
                def session_idx = parts.findIndexOf { it.startsWith('ses-') }
                def full_id = session_idx > 0 ? "${subject_id}_${parts[session_idx]}" : subject_id
                
                tuple(full_id, file)
            }
            .set { t1_images_ch }
        
        // Validate BIDS if requested
        if (params.run_bids_validation) {
            BIDS_VALIDATE(params.bids_dir)
        }
        
    } else {
        // NIfTI input mode (default)
        Channel
            .fromPath("${params.nii_dir}/${params.pattern}")
            .ifEmpty { error "No T1 images found matching ${params.nii_dir}/${params.pattern}" }
            .map { file ->
                // Extract subject ID from filename
                def subject_id = file.name.replaceAll(/_T1w\.nii\.gz$/, '')
                tuple(subject_id, file)
            }
            .set { t1_images_ch }
    }
    
    // Display found subjects
    t1_images_ch.view { subject_id, file ->
        "Found subject: ${subject_id} -> ${file.name}"
    }
    
    // Run MRIQC if requested (requires BIDS input)
    if (params.run_mriqc && params.input_mode == 'bids') {
        bids_subjects_ch = t1_images_ch.map { id, file ->
            def subject_id = id.replaceAll(/^sub-/, '').replaceAll(/_ses-.*$/, '')
            tuple(subject_id, file.parent.parent)
        }
        QC_WORKFLOW(bids_subjects_ch)
    }
    
    // Choose processing mode
    if (params.run_longitudinal) {
        // Longitudinal processing
        LONGITUDINAL_WORKFLOW(t1_images_ch)
        
        // Generate summary
        LONGITUDINAL_WORKFLOW.out.long_dirs
            .map { base_id, tp_id, dir -> tp_id }
            .collect()
            .set { all_subjects }
        
        GENERATE_SUMMARY(
            all_subjects,
            LONGITUDINAL_WORKFLOW.out.slopes,
            LONGITUDINAL_WORKFLOW.out.percent_change,
            'longitudinal'
        )
        
    } else {
        // Cross-sectional processing
        CROSS_SECTIONAL_WORKFLOW(t1_images_ch)
        
        // Generate summary
        CROSS_SECTIONAL_WORKFLOW.out.subject_dirs
            .map { subject_id, dir -> subject_id }
            .collect()
            .set { all_subjects }
        
        GENERATE_SUMMARY(
            all_subjects,
            CROSS_SECTIONAL_WORKFLOW.out.thickness,
            CROSS_SECTIONAL_WORKFLOW.out.volumes,
            'cross-sectional'
        )
    }
}

// ================================================================================
// WORKFLOW COMPLETION
// ================================================================================

workflow.onComplete {
    log.info """\
        ====================================
        Pipeline Execution Complete!
        ====================================
        Status: ${workflow.success ? 'SUCCESS' : 'FAILED'}
        Duration: ${workflow.duration}
        
        Output locations:
        - FastSurfer: ${params.output_dir}
        - Statistics: ${params.stats_dir}
        - QC reports: ${params.qc_dir}
        - Logs: ${projectDir}/logs
        
        Summary: pipeline_summary.txt
        ====================================
        """
        .stripIndent()
}

workflow.onError {
    log.error """\
        ====================================
        Pipeline Execution Failed
        ====================================
        Error message: ${workflow.errorMessage}
        
        Check logs in: ${projectDir}/logs
        Work directory: ${workflow.workDir}
        ====================================
        """
        .stripIndent()
}
