"""
HeuDiConv Heuristic File for DICOM to BIDS Conversion

This heuristic file defines how DICOM series should be converted to BIDS format.
Customize the patterns and rules based on your specific DICOM naming conventions.

Author: HPC Neuroimaging Team
Version: 2.0.0

CUSTOMIZATION INSTRUCTIONS:
1. Examine your DICOM series descriptions using:
   heudiconv -d 'dicom/*/*.dcm' -s SUBJECT_ID -c none -f convertall -o /tmp/heuristic_test
   
2. Look at the .heudiconv/SUBJECT_ID/info/dicominfo.tsv file to see series descriptions

3. Update the criteria dictionaries below to match your series descriptions

4. Test the heuristic:
   heudiconv -d 'dicom/*/*.dcm' -s SUBJECT_ID -c dcm2niix -f heuristic.py -o bids/ -b

For more information: https://heudiconv.readthedocs.io/
"""

import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    """
    Create a key for the conversion
    
    Args:
        template: BIDS template string
        outtype: Output file type(s)
        annotation_classes: Additional annotation classes
        
    Returns:
        Key tuple
    """
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """
    Heuristic evaluator for determining which runs belong where
    
    Args:
        seqinfo: List of sequence information from DICOM headers
        
    Returns:
        Dictionary mapping keys to lists of series
    """
    
    # =========================================================================
    # DEFINE BIDS TEMPLATES
    # =========================================================================
    
    # Anatomical scans
    t1w = create_key('sub-{subject}/anat/sub-{subject}_T1w')
    t1w_ses = create_key('sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w')
    
    t2w = create_key('sub-{subject}/anat/sub-{subject}_T2w')
    t2w_ses = create_key('sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T2w')
    
    flair = create_key('sub-{subject}/anat/sub-{subject}_FLAIR')
    flair_ses = create_key('sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_FLAIR')
    
    # Functional scans
    bold = create_key('sub-{subject}/func/sub-{subject}_task-rest_bold')
    bold_ses = create_key('sub-{subject}/ses-{session}/func/sub-{subject}_ses-{session}_task-rest_bold')
    
    # Diffusion scans
    dwi = create_key('sub-{subject}/dwi/sub-{subject}_dwi')
    dwi_ses = create_key('sub-{subject}/ses-{session}/dwi/sub-{subject}_ses-{session}_dwi')
    
    # Field maps
    fmap_mag = create_key('sub-{subject}/fmap/sub-{subject}_magnitude')
    fmap_mag_ses = create_key('sub-{subject}/ses-{session}/fmap/sub-{subject}_ses-{session}_magnitude')
    
    fmap_phase = create_key('sub-{subject}/fmap/sub-{subject}_phasediff')
    fmap_phase_ses = create_key('sub-{subject}/ses-{session}/fmap/sub-{subject}_ses-{session}_phasediff')
    
    # =========================================================================
    # INITIALIZE OUTPUT DICTIONARY
    # =========================================================================
    
    info = {
        t1w: [],
        t1w_ses: [],
        t2w: [],
        t2w_ses: [],
        flair: [],
        flair_ses: [],
        bold: [],
        bold_ses: [],
        dwi: [],
        dwi_ses: [],
        fmap_mag: [],
        fmap_mag_ses: [],
        fmap_phase: [],
        fmap_phase_ses: []
    }
    
    # =========================================================================
    # DEFINE SERIES MATCHING CRITERIA
    # =========================================================================
    
    # Determine if we have session information
    has_session = False
    for s in seqinfo:
        # Check if session info is in the path or protocol name
        if 'ses-' in str(s.series_description).lower() or 'session' in str(s.series_description).lower():
            has_session = True
            break
    
    # =========================================================================
    # MATCH SERIES TO BIDS TEMPLATES
    # =========================================================================
    
    for s in seqinfo:
        """
        The namedtuple `s` contains the following fields:
        
        * total_files_till_now
        * example_dcm_file
        * series_id
        * dcm_dir_name
        * unspecified2
        * unspecified3
        * dim1
        * dim2
        * dim3
        * dim4
        * TR
        * TE
        * protocol_name
        * is_motion_corrected
        * is_derived
        * patient_id
        * study_description
        * referring_physician_name
        * series_description
        * image_type
        """
        
        # Get series description (lowercase for case-insensitive matching)
        series_desc = str(s.series_description).lower()
        protocol = str(s.protocol_name).lower()
        
        # Skip derived images and motion corrected images
        if s.is_derived or s.is_motion_corrected:
            continue
        
        # =====================================================================
        # T1-WEIGHTED IMAGES
        # =====================================================================
        # Common patterns: 't1', 'mprage', 't1w', 'spgr', '3d t1'
        
        if any(pattern in series_desc for pattern in ['t1', 'mprage', 't1w', 'spgr']) and \
           not any(pattern in series_desc for pattern in ['t2', 'flair', 'scout']):
            if has_session:
                info[t1w_ses].append(s.series_id)
            else:
                info[t1w].append(s.series_id)
        
        # =====================================================================
        # T2-WEIGHTED IMAGES
        # =====================================================================
        # Common patterns: 't2', 't2w', 't2 space'
        
        elif any(pattern in series_desc for pattern in ['t2w', 't2 ', ' t2']) and \
             not any(pattern in series_desc for pattern in ['flair', 't1']):
            if has_session:
                info[t2w_ses].append(s.series_id)
            else:
                info[t2w].append(s.series_id)
        
        # =====================================================================
        # FLAIR IMAGES
        # =====================================================================
        # Common patterns: 'flair', 'dark fluid'
        
        elif 'flair' in series_desc or 'dark fluid' in series_desc:
            if has_session:
                info[flair_ses].append(s.series_id)
            else:
                info[flair].append(s.series_id)
        
        # =====================================================================
        # BOLD/FUNCTIONAL IMAGES
        # =====================================================================
        # Common patterns: 'bold', 'fmri', 'resting', 'rest', 'func'
        
        elif any(pattern in series_desc for pattern in ['bold', 'fmri', 'resting', 'rest', 'func']):
            if has_session:
                info[bold_ses].append(s.series_id)
            else:
                info[bold].append(s.series_id)
        
        # =====================================================================
        # DIFFUSION WEIGHTED IMAGES
        # =====================================================================
        # Common patterns: 'dwi', 'dti', 'diffusion'
        
        elif any(pattern in series_desc for pattern in ['dwi', 'dti', 'diffusion']):
            if has_session:
                info[dwi_ses].append(s.series_id)
            else:
                info[dwi].append(s.series_id)
        
        # =====================================================================
        # FIELD MAPS
        # =====================================================================
        # Common patterns: 'field', 'fmap', 'gre'
        
        elif 'field' in series_desc or 'fmap' in series_desc:
            if 'phase' in series_desc:
                if has_session:
                    info[fmap_phase_ses].append(s.series_id)
                else:
                    info[fmap_phase].append(s.series_id)
            elif 'mag' in series_desc or 'magnitude' in series_desc:
                if has_session:
                    info[fmap_mag_ses].append(s.series_id)
                else:
                    info[fmap_mag].append(s.series_id)
    
    return info


def ReplaceSession(sesname):
    """
    Optional: Replace session names with standardized format
    
    Args:
        sesname: Original session name
        
    Returns:
        Standardized session name
    """
    # Example: Convert various session formats to standard format
    sesname = str(sesname).lower()
    
    if 'baseline' in sesname or 'bl' in sesname:
        return '01'
    elif 'followup' in sesname or 'fu' in sesname:
        return '02'
    elif 'timepoint1' in sesname or 'tp1' in sesname:
        return '01'
    elif 'timepoint2' in sesname or 'tp2' in sesname:
        return '02'
    elif 'timepoint3' in sesname or 'tp3' in sesname:
        return '03'
    else:
        return sesname


def ReplaceSubject(subjname):
    """
    Optional: Replace subject names with standardized format
    
    Args:
        subjname: Original subject name
        
    Returns:
        Standardized subject name
    """
    # Example: Remove common prefixes and ensure zero-padding
    subjname = str(subjname)
    
    # Remove common prefixes
    for prefix in ['sub-', 'subj', 'subject', 'pt', 'patient']:
        if subjname.lower().startswith(prefix):
            subjname = subjname[len(prefix):]
    
    # Zero-pad numeric IDs
    if subjname.isdigit():
        subjname = subjname.zfill(3)  # Pad to 3 digits (e.g., '001')
    
    return subjname


# =============================================================================
# METADATA EXTRACTION (OPTIONAL)
# =============================================================================

def MetadataExtras(seqinfo, metadata):
    """
    Optional: Add extra metadata to JSON sidecars
    
    Args:
        seqinfo: Sequence information
        metadata: Existing metadata dictionary
        
    Returns:
        Updated metadata dictionary
    """
    # Example: Add custom metadata
    metadata['InstitutionName'] = 'Your Institution'
    metadata['InstitutionalDepartmentName'] = 'Neuroimaging Center'
    
    return metadata


# =============================================================================
# NOTES FOR CUSTOMIZATION
# =============================================================================

"""
COMMON CUSTOMIZATION SCENARIOS:

1. MULTIPLE T1 SCANS PER SESSION:
   - Add run numbers to the template:
     t1w_run1 = create_key('sub-{subject}/anat/sub-{subject}_run-01_T1w')
     t1w_run2 = create_key('sub-{subject}/anat/sub-{subject}_run-02_T1w')
   
2. TASK-BASED FMRI:
   - Specify task names:
     bold_task1 = create_key('sub-{subject}/func/sub-{subject}_task-nback_bold')
     bold_task2 = create_key('sub-{subject}/func/sub-{subject}_task-rest_bold')

3. MULTI-ECHO SEQUENCES:
   - Add echo numbers:
     bold_echo1 = create_key('sub-{subject}/func/sub-{subject}_echo-1_bold')
     bold_echo2 = create_key('sub-{subject}/func/sub-{subject}_echo-2_bold')

4. ACQUISITION PARAMETERS:
   - Add acquisition labels:
     t1w_acq1 = create_key('sub-{subject}/anat/sub-{subject}_acq-mprage_T1w')
     t1w_acq2 = create_key('sub-{subject}/anat/sub-{subject}_acq-spgr_T1w')

5. DEBUGGING:
   - Print series information to see what you're matching:
     print(f"Series: {s.series_id}, Description: {s.series_description}")
   - Run with -c none first to see all series without converting

TESTING YOUR HEURISTIC:
1. Test on one subject first:
   heudiconv -d 'dicom/{subject}/*/*.dcm' -s TEST001 -c dcm2niix -f heuristic.py -o bids/ -b

2. Check the output BIDS structure:
   tree bids/

3. Validate with BIDS validator:
   bids-validator bids/

4. Once confirmed, process all subjects
"""

