# -*- coding: utf-8 -*-
"""
Pipeline for group analysis of MEG data
Adapted from Lau Møller Andersen
@author: Martin Schulz
@email: martin.schulz@stud.uni-heidelberg.de
@github: marsipu/mne_pipeline_hd
"""
#%%============================================================================
# IMPORTS
#==============================================================================
import sys
from os import makedirs
from os.path import join, isfile, exists
import re
import numpy as np
import mne

from pipeline_functions import io_functions as io
from pipeline_functions import operations_functions as op
from pipeline_functions import plot_functions as plot
from pipeline_functions import subject_organisation as suborg
from pipeline_functions import utilities as ut
#%%============================================================================
# WHICH SUBJECT? (TO SET)
#==============================================================================
# Which File do you want to run?
# Type in the line of the filename in your sub_list.py
    # Examples:
    # '5' (One File)
    # '1,7,28' (Several Files)
    # '1-5' (From File x to File y)
    # '1-4,7,20-26' (The last two combined)
    # '1-20,!4-6' (1-20 except 4-6)
    # 'all' (All files in sub_list.py)
    # 'all,!4-6' (All files except 4-6)

which_file = '100' # Has to be a string/enclosed in apostrophs
which_mri_subject = '61' # Has to be a string/enclosed in apostrophs
which_erm_file = 'all' # Has to be a string/enclosed in apostrophs
which_motor_erm_file = 'all' # Has to be a string/enclosed in apostrophs
#%%============================================================================
# PARAMETERS (TO SET)
#==============================================================================
#OS
n_jobs = -1 #number of processor-cores to use, -1 for auto
enable_cuda = False # Using CUDA on supported graphics card e.g. for filtering
                    # cupy and appropriate CUDA-Drivers have to be installed
                    # https://mne-tools.github.io/dev/advanced_setup.html#advanced-setup

#File I/O
unspecified_names = True # If you don't use Regular Expressions to handle your filenames

# should files be overwritten
overwrite = True # this counts for all operations below that save output
save_plots = True # should plots be saved

# raw
predefined_bads = [6,7,8,26,27,28,79,97,103]
eog_digitized = True # Set True, if the last 4 digitized points where EOG
lowpass = 80 # Hz
highpass = 1 # Hz # at least 1 if to apply ICA

# events
adjust_timeline_by_msec = -95 #delay to stimulus in ms

# epochs
min_duration = 0.005 # s
time_unit = 's'
tmin = -0.500 # s
tmax = 2.000 # s
baseline = (-0.500, -0.100) # [s]
autoreject = 1 # set 1 for autoreject
overwrite_ar = 0 # if to calculate new thresholds or to use previously calculated
reject = dict(grad=8000e-13) # if not reject with autoreject
flat = dict(grad=1e-15)
reject_eog_epochs=False
decim = 1 # downsampling factor
event_id = {'LBT':1, 'offset':4, 'lower_R':5, 'same_R':6, 'higher_R':7}

# evokeds
ica_evokeds = True
detrend = False # somehow not working on all data

#Time-Frequency-Analysis
tfr_freqs = np.arange(5,100,5)
overwrite_tfr = False
tfr_method = 'morlet'
multitaper_bandwith = 4.0
stockwell_width = 1.0

#ICA
eog_channel = 'EEG 001'
ecg_channel = 'EEG 003'

# forward modeling
source_space_method = 'ico5'

# source reconstruction
use_calm_cov = False
erm_ica = False # Causes sometimes errors
method = 'dSPM'
mne_evoked_time = [0, 0.05, 0.1, 0.15, 0.2] # s
stc_interactive = False
stc_animation = [0,0.5] # s
eeg_fwd = False
parcellation = 'aparc.a2009s'
con_methods = ['coh', 'pli', 'wpli2_debiased']
con_fmin = 30
con_fmax = 60

# Dipole-fit
ECDs = {}
ECD_min = 0.200
ECD_max = 0.250

target_labels = {'lh':['S_central-lh', 'S_postcentral-lh', 'S_circular_insula_sup-lh',
                       'S_temporal_sup-lh'],
                 'rh':['S_central-rh', 'S_postcentral-rh', 'S_circular_insula_sup-rh',
                       'S_temporal_sup-rh']}

# grand averages
morph_to='fsaverage' # name of the freesurfer subject to be morphed to
fuse_ab = True

# statistics
independent_variable_1 = 'standard_3'
independent_variable_2 = 'non_stimulation'
time_window = (0.050, 0.060)
n_permutations = 10000 # specify as integer

# statistics plotting
p_threshold = 1e-15 # 1e-15 is the smallest it can get for the way it is coded

# freesurfer and MNE-C commands
n_jobs_freesurfer = 4 # change according to amount of processors you have available
#%%============================================================================
# GUI CALL
#==============================================================================
exec_ops = ut.choose_function()
#%%============================================================================
# PATHS (TO SET)
#==============================================================================
# specify the path to a general analysis folder according to your OS
if sys.platform == 'win32':
    home_path = 'D:/Promotion' # A folder to put your MNE-Projects in
if sys.platform == 'linux':
    home_path = '/mnt/d/Promotion'

project_name = 'Test' # specify the name for your project as a folder
subjects_dir = join(home_path, 'Freesurfer/Output') # name of your
orig_data_path = join(home_path, 'Test/Dateien')
#%%============================================================================
# DEPENDING PATHS (NOT TO SET)
#==============================================================================
data_path = join(home_path, project_name, 'Daten')
sub_script_path = join(data_path, '_Subject_scripts')
mne.utils.set_config("SUBJECTS_DIR", subjects_dir, set_env=True)
save_dir_averages = join(data_path,'grand_averages')

if exec_ops['erm_analysis'] or exec_ops['motor_erm_analysis']:
    figures_path = join(home_path, project_name, 'Figures/ERM_Figures')    
else:
    figures_path = join(home_path, project_name, 'Figures/')

#add subjects, mri_subjects, sub_dict, bad_channels_dict
sub_list_path = join(sub_script_path, 'sub_list.py')
erm_list_path = join(sub_script_path, 'erm_list.py') # ERM means Empty-Room
motor_erm_list_path = join(sub_script_path, 'motor_erm_list.py') # Special for Pinprick
mri_sub_list_path = join(sub_script_path, 'mri_sub_list.py')
sub_dict_path = join(sub_script_path, 'sub_dict.py')
erm_dict_path = join(sub_script_path, 'erm_dict.py')
bad_channels_dict_path = join(sub_script_path, 'bad_channels_dict.py')

path_list = [subjects_dir, orig_data_path, data_path, sub_script_path,
             figures_path]
file_list = [sub_list_path, erm_list_path, motor_erm_list_path, mri_sub_list_path,
             sub_dict_path, erm_dict_path, bad_channels_dict_path]

if not exists(home_path):
    print('Create home_path manually and set the variable accordingly')
    
for p in path_list:
    if not exists(p):
        makedirs(p)
        print(f'{p} created')

for f in file_list:
    if not isfile(f):
        with open(f, 'w') as file:
            file.write('')
        print(f'{f} created')
        
op.populate_directories(data_path, figures_path, event_id)
#%%============================================================================
# SUBJECT ORGANISATION (NOT TO SET)
#==============================================================================
if exec_ops['add_subjects']: # set 1 to run
    suborg.add_subjects(sub_list_path, erm_list_path, motor_erm_list_path,
                        data_path, figures_path, subjects_dir, orig_data_path,
                        unspecified_names, gui=False)

if exec_ops['add_mri_subjects']: # set 1 to run
    suborg.add_mri_subjects(subjects_dir, mri_sub_list_path, data_path, gui=False)

if exec_ops['add_sub_dict']: # set 1 to run
    suborg.add_sub_dict(sub_dict_path, sub_list_path, mri_sub_list_path, data_path)

if exec_ops['add_erm_dict']: #set 1 to run
    suborg.add_erm_dict(erm_dict_path, sub_list_path, erm_list_path, data_path)

if exec_ops['add_bad_channels']:
    suborg.add_bad_channels_dict(bad_channels_dict_path, sub_list_path,
                                 erm_list_path, motor_erm_list_path,
                                 data_path, predefined_bads,
                                 sub_script_path)

#Subject-Functions
all_subjects = suborg.read_subjects(sub_list_path)
all_mri_subjects = suborg.read_mri_subjects(mri_sub_list_path)
erm_files = suborg.read_subjects(erm_list_path)
motor_erm_files = suborg.read_subjects(motor_erm_list_path)
sub_to_mri = suborg.read_sub_dict(sub_dict_path)
erm_dict = suborg.read_sub_dict(erm_dict_path) # add None if not available
bad_channels_dict = suborg.read_bad_channels_dict(bad_channels_dict_path)
#%%========================================================================
# MRI-Subjects (NOT TO SET)
#============================================================================
if exec_ops['mri_preprocessing']:

    mri_subjects = suborg.mri_subject_selection(which_mri_subject, all_mri_subjects)

    print('Selected MRI-Subjects:')
    for i in mri_subjects:
        print(i)

    for mri_subject in mri_subjects:
        print('='*60 + '\n', mri_subject)

        #==========================================================================
        # BASH SCRIPTS
        #==========================================================================
        if exec_ops['apply_watershed']:
            op.apply_watershed(mri_subject, subjects_dir, overwrite)

        if exec_ops['make_dense_scalp_surfaces']:
            op.make_dense_scalp_surfaces(mri_subject, subjects_dir, overwrite)

        #==========================================================================
        # Forward Modeling
        #==========================================================================
        if exec_ops['setup_source_space']:
            op.setup_source_space(mri_subject, subjects_dir, source_space_method,
                           overwrite, n_jobs)
        
        if exec_ops['prepare_bem']:
            op.prepare_bem(mri_subject, subjects_dir, overwrite)
            
        if exec_ops['morph_subject']:
            op.morph_subject(mri_subject, subjects_dir, morph_to,
                             source_space_method, overwrite)
            
        #==========================================================================
        # PLOT SOURCE SPACES
        #==========================================================================

        if exec_ops['plot_source_space']:
            plot.plot_source_space(mri_subject, subjects_dir, source_space_method, save_plots, figures_path)

        if exec_ops['plot_bem']:
            plot.plot_bem(mri_subject, subjects_dir, source_space_method, figures_path,
                          save_plots)
            
        if exec_ops['plot_labels']:
            plot.plot_labels(mri_subject, subjects_dir, save_plots, figures_path,
                             parcellation)
            
        # close plots
        if exec_ops['close_plots']:
            plot.close_all()
#%%========================================================================
# Subjects (NOT TO SET)
#===========================================================================
if exec_ops['erm_analysis']:
    subjects = suborg.file_selection(which_erm_file, erm_files)   
if exec_ops['motor_erm_analysis']:
    subjects = suborg.file_selection(which_motor_erm_file, motor_erm_files)
else:
    subjects = suborg.file_selection(which_file, all_subjects)


if len(all_subjects)==0:
    print('No subjects in sub_list!')
    print('Add some folders(the ones with the date) to your orig_data_path-folder and check "add_subjects"')
else:
    print('Selected Subjects:')
    for s in subjects:
        print(s)

# Get dicts grouping the subjects together depending on their names to allow grand_averaging:
ab_dict, comp_dict, grand_avg_dict = ut.get_subject_groups(subjects, fuse_ab)

morphed_data_all = dict(LBT=[], offset=[], lower_R=[], same_R=[], higher_R=[])

for name in subjects:
    # Print Subject Console Header
    print(60*'='+'\n'+name)
    
    if exec_ops['erm_analysis'] or exec_ops['motor_erm_analysis']:
        save_dir = join(data_path, 'empty_room_data')
    else:
        save_dir = join(data_path, name)       
    
    # Use Regular Expressions to make ermsub and subtomri assignement easier
    pattern = r'pp[0-9]+[a-z]?'
    if unspecified_names:
        pattern = r'.*'
    match = re.match(pattern, name)
    prefix = match.group()
    
    try:
        ermsub = erm_dict[prefix]
    except KeyError as k:
        print(f'No erm_measurement for {k}')
        suborg.add_erm_dict(erm_dict_path, sub_list_path, data_path)
    
    try:
        subtomri = sub_to_mri[prefix]
    except KeyError as k:
        print(f'No mri_subject assigned to {k}')
        suborg.add_sub_dict(sub_dict_path, sub_list_path, data_path)
        
    try:
        bad_channels = bad_channels_dict[name]
    except KeyError as k:
        print(f'No bad channels for {k}')
        suborg.add_bad_channels_dict(bad_channels_dict_path, sub_list_path,
                                     erm_list_path, motor_erm_list_path,
                                     data_path, predefined_bads,
                                     sub_script_path)

    #==========================================================================
    # FILTER RAW
    #==========================================================================

    if exec_ops['filter_raw']:
        op.filter_raw(name, save_dir, lowpass, highpass, overwrite, ermsub,
                              data_path, n_jobs, enable_cuda, bad_channels)

    #==========================================================================
    # FIND EVENTS
    #==========================================================================

    if exec_ops['find_events']:
        op.find_events_pp(name, save_dir, min_duration,
                          adjust_timeline_by_msec,lowpass, highpass, overwrite,
                          save_plots, figures_path)

    if exec_ops['find_eog_events']:
        op.find_eog_events(name, save_dir, eog_channel)

    #==========================================================================
    # EPOCHS
    #==========================================================================

    if exec_ops['epoch_raw']:
        op.epoch_raw(name, save_dir, lowpass, highpass, event_id, tmin, tmax,
                     baseline, reject, flat, autoreject, overwrite_ar,
                     sub_script_path, bad_channels, decim,
                     reject_eog_epochs, overwrite)

    #==========================================================================
    # SIGNAL SPACE PROJECTION
    #==========================================================================
    if exec_ops['run_ssp_er']:
        op.run_ssp_er(name, save_dir, lowpass, highpass, data_path, ermsub, bad_channels,
                      eog_channel, ecg_channel, overwrite)

    if exec_ops['apply_ssp_er']:
        op.apply_ssp_er(name, save_dir,lowpass, highpass, overwrite)

    if exec_ops['run_ssp_clm']:
        op.run_ssp_clm(name, save_dir, lowpass, highpass, bad_channels, overwrite)

    if exec_ops['apply_ssp_clm']:
        op.apply_ssp_clm(name, save_dir, lowpass, highpass, overwrite)

    if exec_ops['run_ssp_eog']:
        op.run_ssp_eog(name, save_dir, lowpass, highpass, n_jobs, eog_channel,
                                   bad_channels, overwrite)

    if exec_ops['apply_ssp_eog']:
        op.apply_ssp_eog(name, save_dir, lowpass, highpass, overwrite)

    if exec_ops['run_ssp_ecg']:
        op.run_ssp_ecg(name, save_dir,lowpass, highpass, n_jobs, ecg_channel,
                                   bad_channels, overwrite)

    if exec_ops['apply_ssp_ecg']:
        op.apply_ssp_ecg(name, save_dir,lowpass, highpass, overwrite)

    if exec_ops['plot_ssp']:
        plot.plot_ssp(name, save_dir,lowpass, highpass, save_plots,
                      figures_path, bad_channels, ermsub)

    if exec_ops['plot_ssp_eog']:
        plot.plot_ssp_eog(name, save_dir,lowpass, highpass, save_plots,
                              figures_path, bad_channels)

    if exec_ops['run_ica']:
        op.run_ica(name, save_dir,lowpass, highpass, eog_channel, ecg_channel,
                           reject, flat, bad_channels, overwrite, autoreject,
                           save_plots, figures_path, sub_script_path,
                           exec_ops['erm_analysis'])

    #==========================================================================
    # LOAD NON-ICA'ED EPOCHS AND APPLY ICA
    #==========================================================================

    if exec_ops['apply_ica']:
        op.apply_ica(name, save_dir,lowpass, highpass, data_path,
                     overwrite)

    #==========================================================================
    # EVOKEDS
    #==========================================================================

    if exec_ops['get_evokeds']:
        op.get_evokeds(name, save_dir,lowpass, highpass, exec_ops, ermsub,
                       detrend, ica_evokeds, overwrite)
    
    #==========================================================================
    # TIME-FREQUENCY-ANALASYS
    #==========================================================================
    
    if exec_ops['tfr']:
        op.tfr(name, save_dir, lowpass, highpass, ica_evokeds, tfr_freqs, overwrite_tfr,
               tfr_method, multitaper_bandwith, stockwell_width, n_jobs)

    #==========================================================================
    # NOISE COVARIANCE MATRIX
    #==========================================================================

    if exec_ops['estimate_noise_covariance']:
        op.estimate_noise_covariance(name, save_dir,lowpass, highpass, overwrite,
                                     ermsub, data_path, bad_channels, n_jobs,
                                     use_calm_cov, ica_evokeds, erm_ica)

    if exec_ops['plot_noise_covariance']:
        plot.plot_noise_covariance(name, save_dir,lowpass, highpass,
                                   subtomri, save_plots, figures_path, ermsub,
                                   use_calm_cov)

    #==========================================================================
    # CO-REGISTRATION
    #==========================================================================

    # use mne.gui.coregistration()

    if exec_ops['mri_coreg']:
        op.mri_coreg(name, save_dir, subtomri, subjects_dir, eog_digitized)

    if exec_ops['plot_transformation']:
        plot.plot_transformation(name, save_dir, subtomri, subjects_dir,
                                 save_plots, figures_path)

    #==========================================================================
    # CREATE FORWARD MODEL
    #==========================================================================

    if exec_ops['create_forward_solution']:
        op.create_forward_solution(name, save_dir, subtomri, subjects_dir,
                                           source_space_method, overwrite,
                                           n_jobs, eeg_fwd)

    #==========================================================================
    # CREATE INVERSE OPERATOR
    #==========================================================================

    if exec_ops['create_inverse_operator']:
        op.create_inverse_operator(name, save_dir,lowpass, highpass,
                                        overwrite, ermsub, use_calm_cov)

    #==========================================================================
    # SOURCE ESTIMATE MNE
    #==========================================================================

    if exec_ops['source_estimate']:
        op.source_estimate(name, save_dir,lowpass, highpass, method, overwrite)

    if exec_ops['vector_source_estimate']:
        op.vector_source_estimate(name, save_dir,lowpass, highpass, method, overwrite)

    if exec_ops['ECD_fit']:
        op.ECD_fit(name, save_dir,lowpass, highpass, ermsub, subjects_dir,
                           subtomri, source_space_method, use_calm_cov, ECDs,
                           n_jobs, target_labels, save_plots, figures_path)
    
    if exec_ops['apply_morph']:
        stcs = op.apply_morph(name, save_dir, lowpass, highpass,
                              subjects_dir, subtomri, method,
                              overwrite, n_jobs, morph_to,
                              source_space_method, event_id)
        
    #==========================================================================
    # PRINT INFO
    #==========================================================================
    
    if exec_ops['print_info']:
        plot.print_info(name, save_dir, save_plots)

    if exec_ops['plot_sensors']:
        plot.plot_sensors(name, save_dir)

    #==========================================================================
    # PLOT RAW DATA
    #==========================================================================

    if exec_ops['plot_raw']:
        plot.plot_raw(name, save_dir, overwrite, bad_channels, bad_channels_dict)

    if exec_ops['plot_filtered']:
        plot.plot_filtered(name, save_dir, lowpass, highpass, bad_channels)

    if exec_ops['plot_events']:
        plot.plot_events(name, save_dir, save_plots, figures_path, event_id)

    if exec_ops['plot_events_diff']:
        plot.plot_events_diff(name, save_dir, save_plots, figures_path)

    if exec_ops['plot_eog_events']:
        plot.plot_eog_events(name, save_dir)

    #==========================================================================
    # PLOT POWER SPECTRA
    #==========================================================================

    if exec_ops['plot_power_spectra']:
        plot.plot_power_spectra(name, save_dir,lowpass, highpass,
                                save_plots, figures_path, bad_channels)

    if exec_ops['plot_power_spectra_epochs']:
        plot.plot_power_spectra_epochs(name, save_dir,lowpass, highpass,
                                       save_plots, figures_path, bad_channels)

    if exec_ops['plot_power_spectra_topo']:
        plot.plot_power_spectra_topo(name, save_dir,lowpass, highpass,
                                     save_plots, figures_path, bad_channels)

    #==========================================================================
    # PLOT TIME-FREQUENCY-ANALASYS
    #==========================================================================
    
    if exec_ops['plot_tfr']:
        plot.plot_tfr(name, save_dir, lowpass, highpass, tmin, tmax, baseline,
                      tfr_method, save_plots, figures_path)
    
    if exec_ops['tfr_event_dynamics']:
        plot.tfr_event_dynamics(name, save_dir, tmin, tmax, save_plots,
                                figures_path, bad_channels, n_jobs)
        
    #==========================================================================
    # PLOT CLEANED EPOCHS
    #==========================================================================
    if exec_ops['plot_epochs']:
        plot.plot_epochs(name, save_dir,lowpass, highpass, save_plots,
                               figures_path)

    if exec_ops['plot_epochs_image']:
        plot.plot_epochs_image(name, save_dir,lowpass, highpass, save_plots,
                               figures_path)

    if exec_ops['plot_epochs_topo']:
        plot.plot_epochs_topo(name, save_dir,lowpass, highpass, save_plots,
                              figures_path)
    
    if exec_ops['plot_epochs_drop_log']:
        plot.plot_epochs_drop_log(name, save_dir, lowpass, highpass, save_plots,
                                  figures_path)
    #==========================================================================
    # PLOT EVOKEDS
    #==========================================================================

    if exec_ops['plot_evoked_topo']:
        plot.plot_evoked_topo(name, save_dir,lowpass, highpass, save_plots,
                              figures_path)

    if exec_ops['plot_evoked_topomap']:
        plot.plot_evoked_topomap(name, save_dir,lowpass, highpass, save_plots,
                                 figures_path)

    if exec_ops['plot_butterfly_evokeds']:
        plot.plot_butterfly_evokeds(name, save_dir,lowpass, highpass,
                                    save_plots, figures_path,
                                    time_unit, ermsub, use_calm_cov)

    if exec_ops['plot_evoked_field']:
        plot.plot_evoked_field(name, save_dir,lowpass, highpass, subtomri,
                               subjects_dir, save_plots, figures_path,
                               mne_evoked_time, n_jobs)

    if exec_ops['plot_evoked_joint']:
        plot.plot_evoked_joint(name, save_dir,lowpass, highpass, save_plots,
                               figures_path, ECDs)

    if exec_ops['plot_evoked_white']:
        plot.plot_evoked_white(name, save_dir,lowpass, highpass,
                               save_plots, figures_path, ermsub, use_calm_cov)

    if exec_ops['plot_evoked_image']:
        plot.plot_evoked_image(name, save_dir,lowpass, highpass,
                               save_plots, figures_path)

    #==========================================================================
    # PLOT SOURCE ESTIMATES MNE
    #==========================================================================

    if exec_ops['plot_source_estimates']:
        plot.plot_source_estimates(name, save_dir,lowpass, highpass,
                                      subtomri, subjects_dir,
                                      method, mne_evoked_time, event_id,
                                      stc_interactive, save_plots, figures_path)

    if exec_ops['plot_vector_source_estimates']:
        plot.plot_vector_source_estimates(name, save_dir,lowpass, highpass,
                                      subtomri, subjects_dir,
                                      method, mne_evoked_time,
                                      save_plots, figures_path)

    if exec_ops['plot_animated_stc']:
        plot.plot_animated_stc(name, save_dir,lowpass, highpass, subtomri,
                               subjects_dir, method, mne_evoked_time,
                               stc_animation, tmin, tmax, event_id,
                               save_plots, figures_path)

    if exec_ops['plot_snr']:
        plot.plot_snr(name, save_dir,lowpass, highpass, save_plots, figures_path)

    if exec_ops['label_time_course']:
        plot.label_time_course(name, save_dir, lowpass, highpass, subtomri,
                               target_labels, save_plots, figures_path,
                               parcellation)

    #==========================================================================
    # TIME-FREQUENCY IN SOURCE SPACE
    #==========================================================================
    
    if exec_ops['tf_label_power_phlck']:
        plot.tf_label_power_phlck(name, save_dir, lowpass, highpass, subtomri,
                                  parcellation, save_plots, figures_path, n_jobs)
        
    if exec_ops['source_space_connectivity']:
        op.source_space_connectivity(name, save_dir, lowpass, highpass,
                                     subtomri, subjects_dir, method,
                                     con_methods, con_fmin, con_fmax,
                                     n_jobs, overwrite)
        
    if exec_ops['plot_source_space_connectivity']:
        plot.plot_source_space_connectivity(name, save_dir, lowpass, highpass,
                                   subtomri, subjects_dir, con_methods, con_fmin,
                                   con_fmax, save_plots, figures_path, n_jobs)

    #==========================================================================
    # General Statistics
    #==========================================================================
    if exec_ops['corr_ntr']:
        op.corr_ntr(name, save_dir, lowpass, highpass, exec_ops,
                    ermsub, subtomri, ica_evokeds, save_plots, figures_path)
        
    # close all plots
    if exec_ops['close_plots']:
        plot.close_all()

# GOING OUT OF SUBJECT LOOP

if exec_ops['cmp_label_time_course']:
    plot.cmp_label_time_course(data_path, lowpass, highpass, sub_to_mri, comp_dict,
                               parcellation, target_labels, save_plots, figures_path)

#%%============================================================================
# GRAND AVERAGES (sensor space and source space)
#================================================================================

if exec_ops['grand_avg_evokeds']:
    op.grand_avg_evokeds(data_path, grand_avg_dict, save_dir_averages,
                         lowpass, highpass)

if exec_ops['grand_avg_tfr']:
    op.grand_avg_tfr(data_path, grand_avg_dict, save_dir_averages,
                     lowpass, highpass, tfr_method)

if exec_ops['grand_avg_morphed']:
    op.grand_avg_morphed(grand_avg_dict, data_path, method, save_dir_averages,
                         lowpass, highpass, event_id)

if exec_ops['grand_avg_connect']:
    op.grand_avg_connect(grand_avg_dict, data_path, con_methods,
                         con_fmin, con_fmax, save_dir_averages,
                         lowpass, highpass)
    
#%%============================================================================
# GRAND AVERAGES PLOTS (sensor space and source space)
#================================================================================

if exec_ops['plot_grand_avg_evokeds']:
    plot.plot_grand_avg_evokeds(lowpass, highpass, save_dir_averages, grand_avg_dict,
                                    event_id, save_plots, figures_path)

if exec_ops['plot_grand_avg_tfr']:
    plot.plot_grand_avg_tfr(lowpass, highpass, baseline, tmin, tmax,
                           save_dir_averages, grand_avg_dict,
                           event_id, save_plots, figures_path)

if exec_ops['plot_grand_avg_stc']:
    plot.plot_grand_avg_stc(lowpass, highpass, save_dir_averages,
                            grand_avg_dict, mne_evoked_time, morph_to,
                            subjects_dir, event_id, save_plots,
                            figures_path)

if exec_ops['plot_grand_avg_stc_anim']:
    plot.plot_grand_avg_stc_anim(lowpass, highpass, save_dir_averages,
                                 grand_avg_dict, stc_animation, morph_to,
                                 subjects_dir, event_id, save_plots,
                                 figures_path)

if exec_ops['plot_grand_avg_connect']:
    plot.plot_grand_avg_connect(lowpass, highpass, save_dir_averages,
                                grand_avg_dict, subjects_dir, morph_to, event_id,
                                con_methods, con_fmin, con_fmax,
                                save_plots, figures_path)
#==============================================================================
# STATISTICS SOURCE SPACE
#==============================================================================

if exec_ops['statistics_source_space']:
    op.statistics_source_space(morphed_data_all, save_dir_averages,
                                       independent_variable_1,
                                       independent_variable_2,
                                       time_window, n_permutations,lowpass, highpass,
                                       overwrite)

#==============================================================================
# PLOT GRAND AVERAGES OF SOURCE ESTIMATES WITH STATISTICS CLUSTER MASK
#==============================================================================

if exec_ops['plot_grand_averages_source_estimates_cluster_masked']:
    plot.plot_grand_averages_source_estimates_cluster_masked(
        name, save_dir_averages,lowpass, highpass, subjects_dir, method, time_window,
        save_plots, figures_path, independent_variable_1,
        independent_variable_2, mne_evoked_time, p_threshold)

# close all plots
if exec_ops['close_plots']:
    plot.close_all()