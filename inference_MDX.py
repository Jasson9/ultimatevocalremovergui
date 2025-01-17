import os
import subprocess
from unittest import skip
from pathlib import Path
import os.path
from datetime import datetime
import pydub
import shutil
import hashlib

#MDX-Net
#----------------------------------------
import soundfile as sf
import torch
import numpy as np

from demucs.pretrained import get_model as _gm
from demucs.hdemucs import HDemucs
from demucs.apply import BagOfModels, apply_model
from demucs.audio import AudioFile
import pathlib

from models import get_models, spec_effects
import onnxruntime as ort
import time
import os
from tqdm import tqdm
import warnings
import sys
import librosa
import psutil
#----------------------------------------
from lib_v5 import spec_utils
from lib_v5.model_param_init import ModelParameters
import torch

# Command line text parsing and widget manipulation
import tkinter as tk
import traceback  # Error Message Recent Calls
import time  # Timer

from typing import Literal
    
class Predictor():        
    def __init__(self):
        pass
    
    def prediction_setup(self):
        
        global device

        print('Print the gpu setting: ', data['gpu'])

        if data['gpu'] >= 0:
            device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')   
        if data['gpu'] == -1:
            device = torch.device('cpu')
        
        if data['demucsmodel']:
            if 'UVR' in demucs_model_set:
                self.demucs = HDemucs(sources=["other", "vocals"])
            else:
                self.demucs = HDemucs(sources=["drums", "bass", "other", "vocals"])
            widget_text.write(base_text + 'Loading Demucs model...')
            update_progress(**progress_kwargs,
            step=0.05)   
            path_d = Path('models/Demucs_Models')
            self.demucs = _gm(name=demucs_model_set, repo=path_d)
            self.demucs.to(device)
            self.demucs.eval()
            widget_text.write('Done!\n')
            if isinstance(self.demucs, BagOfModels):
                widget_text.write(base_text + f"Selected Demucs model is a bag of {len(self.demucs.models)} model(s).\n")

        self.onnx_models = {}
        c = 0
        
        self.models = get_models('tdf_extra', load=False, device=cpu, stems=modeltype, n_fft_scale=n_fft_scale_set, dim_f=dim_f_set)
        if not data['demucs_only']:
            widget_text.write(base_text + 'Loading ONNX model... ')
        
        update_progress(**progress_kwargs,
        step=0.1)
        c+=1
        
        if data['gpu'] >= 0:
            if torch.cuda.is_available():
                run_type = ['CUDAExecutionProvider']
            else:
                data['gpu'] = -1
                widget_text.write("\n" + base_text + "No NVIDIA GPU detected. Switching to CPU... ")    
                run_type = ['CPUExecutionProvider']     
        elif data['gpu'] == -1:
            run_type = ['CPUExecutionProvider']
            
        print('Selected Model: ', model_set)
        self.onnx_models[c] = ort.InferenceSession(os.path.join('models/MDX_Net_Models', str(model_set) + '.onnx'), providers=run_type)
        
        if not data['demucs_only']:
            widget_text.write('Done!\n')
        
    def prediction(self, m):  
        mix, samplerate = librosa.load(m, mono=False, sr=44100)
        if mix.ndim == 1:
            mix = np.asfortranarray([mix,mix])  
        samplerate = samplerate
        mix = mix.T
        sources = self.demix(mix.T)
        widget_text.write(base_text + 'Inferences complete!\n')
        c = -1
    
        #Main Save Path
        save_path = os.path.dirname(_basename)
        
        print('stemset_n: ', stemset_n)
        
        #Vocal Path
        if stemset_n == '(Vocals)':
            vocal_name = '(Vocals)'
        elif stemset_n == '(Other)':
            vocal_name = '(Other)'
        elif stemset_n == '(Drums)':
            vocal_name = '(Drums)'
        elif stemset_n == '(Bass)':
            vocal_name = '(Bass)'
            
        if data['modelFolder']:
            vocal_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}',)
            vocal_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}',)
            vocal_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}',)
        else:
            vocal_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}',)
            vocal_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}',)
            vocal_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}',)
        
        #Instrumental Path

        if stemset_n == '(Vocals)':
            Instrumental_name = '(Instrumental)'
        elif stemset_n == '(Other)':
            Instrumental_name = '(No_Other)'
        elif stemset_n == '(Drums)':
            Instrumental_name = '(No_Drums)'
        elif stemset_n == '(Bass)':
            Instrumental_name = '(No_Bass)'

        if data['modelFolder']:
            Instrumental_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}_{model_set_name}',)
            Instrumental_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}_{model_set_name}',)
            Instrumental_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}_{model_set_name}',)            
        else: 
            Instrumental_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}',)
            Instrumental_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}',)
            Instrumental_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{Instrumental_name}',)   
                     
        #Non-Reduced Vocal Path
        if stemset_n == '(Vocals)':
            vocal_name = '(Vocals)'
        elif stemset_n == '(Other)':
            vocal_name = '(Other)'
        elif stemset_n == '(Drums)':
            vocal_name = '(Drums)'
        elif stemset_n == '(Bass)':
            vocal_name = '(Bass)'

        if data['modelFolder']:
            non_reduced_vocal_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}_No_Reduction',)
            non_reduced_vocal_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}_No_Reduction',)
            non_reduced_vocal_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_{model_set_name}_No_Reduction',)
        else:
            non_reduced_vocal_path = '{save_path}/{file_name}.wav'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_No_Reduction',)
            non_reduced_vocal_path_mp3 = '{save_path}/{file_name}.mp3'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_No_Reduction',)
            non_reduced_vocal_path_flac = '{save_path}/{file_name}.flac'.format(
                save_path=save_path,
                file_name = f'{os.path.basename(_basename)}_{vocal_name}_No_Reduction',)
            
            
        if os.path.isfile(non_reduced_vocal_path):
            file_exists_n = 'there'
        else:
            file_exists_n = 'not_there'

        if os.path.isfile(vocal_path):
            file_exists_v = 'there'
        else:
            file_exists_v = 'not_there'
            
        if os.path.isfile(Instrumental_path):
            file_exists_i = 'there'
        else:
            file_exists_i = 'not_there'

        print('Is there already a voc file there? ', file_exists_v)

        if not data['noisereduc_s'] == 'None':
            c += 1

            if not data['demucsmodel']:
                if data['inst_only']:
                    widget_text.write(base_text + 'Preparing to save Instrumental...')
                else:
                    widget_text.write(base_text + 'Saving vocals... ')

                sf.write(non_reduced_vocal_path, sources[c].T, samplerate)
                update_progress(**progress_kwargs,
                step=(0.9))
                widget_text.write('Done!\n')        
                widget_text.write(base_text + 'Performing Noise Reduction... ')
                reduction_sen = float(int(data['noisereduc_s'])/10)
                subprocess.call("lib_v5\\sox\\sox.exe" + ' "' + 
                            f"{str(non_reduced_vocal_path)}"  + '" "' + f"{str(vocal_path)}" + '" ' + 
                            "noisered lib_v5\\sox\\" + noise_pro_set + ".prof " + f"{reduction_sen}", 
                            shell=True, stdout=subprocess.PIPE,
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                widget_text.write('Done!\n')        
                update_progress(**progress_kwargs,
                step=(0.95))
            else:
                if data['inst_only']:
                    widget_text.write(base_text + 'Preparing Instrumental...')
                else:
                    widget_text.write(base_text + 'Saving Vocals... ')

                if data['demucs_only']:
                    if 'UVR' in demucs_model_set:
                        sf.write(non_reduced_vocal_path, sources[1].T, samplerate)
                else:
                    sf.write(non_reduced_vocal_path, sources[source_val].T, samplerate)
                update_progress(**progress_kwargs,
                step=(0.9))
                widget_text.write('Done!\n')
                widget_text.write(base_text + 'Performing Noise Reduction... ')
                reduction_sen = float(data['noisereduc_s'])/10
                print(noise_pro_set)
                subprocess.call("lib_v5\\sox\\sox.exe" + ' "' + 
                            f"{str(non_reduced_vocal_path)}"  + '" "' + f"{str(vocal_path)}" + '" ' + 
                            "noisered lib_v5\\sox\\" + noise_pro_set + ".prof " + f"{reduction_sen}", 
                            shell=True, stdout=subprocess.PIPE,
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                update_progress(**progress_kwargs,
                step=(0.95))
                widget_text.write('Done!\n')   
        else:
            c += 1

            if not data['demucsmodel']:
                if data['inst_only']:
                    widget_text.write(base_text + 'Preparing Instrumental...')
                else:
                    widget_text.write(base_text + 'Saving Vocals... ')
                sf.write(vocal_path, sources[c].T, samplerate)
                update_progress(**progress_kwargs,
                step=(0.9))
                widget_text.write('Done!\n')
            else:
                if data['inst_only']:
                    widget_text.write(base_text + 'Preparing Instrumental...')
                else:
                    widget_text.write(base_text + 'Saving Vocals... ')
                    
                if data['demucs_only']:
                    if 'UVR' in demucs_model_set:
                        sf.write(vocal_path, sources[1].T, samplerate)
                    else:
                        sf.write(vocal_path, sources[source_val].T, samplerate)
                else:
                    sf.write(vocal_path, sources[source_val].T, samplerate)
                    
                update_progress(**progress_kwargs,
                step=(0.9))
                widget_text.write('Done!\n')
        
        if data['voc_only'] and not data['inst_only']:
            pass

        else:
            finalfiles = [
                {
                    'model_params':'lib_v5/modelparams/1band_sr44100_hl512.json',
                    'files':[str(music_file), vocal_path],
                }
            ]         
            widget_text.write(base_text + 'Saving Instrumental... ')      
            for i, e in tqdm(enumerate(finalfiles)):

                wave, specs = {}, {}
                        
                mp = ModelParameters(e['model_params'])
                
                for i in range(len(e['files'])):    
                    spec = {}
                    
                    for d in range(len(mp.param['band']), 0, -1):          
                        bp = mp.param['band'][d]            
                        
                        if d == len(mp.param['band']): # high-end band                
                            wave[d], _ = librosa.load(
                                e['files'][i], bp['sr'], False, dtype=np.float32, res_type=bp['res_type'])
                            
                            if len(wave[d].shape) == 1: # mono to stereo
                                wave[d] = np.array([wave[d], wave[d]])
                        else: # lower bands
                            wave[d] = librosa.resample(wave[d+1], mp.param['band'][d+1]['sr'], bp['sr'], res_type=bp['res_type'])
                                
                        spec[d] = spec_utils.wave_to_spectrogram(wave[d], bp['hl'], bp['n_fft'], mp.param['mid_side'], mp.param['mid_side_b2'], mp.param['reverse'])
                        
                    specs[i] = spec_utils.combine_spectrograms(spec, mp)
                
                del wave   
                
                ln = min([specs[0].shape[2], specs[1].shape[2]])
                specs[0] = specs[0][:,:,:ln]
                specs[1] = specs[1][:,:,:ln]
                X_mag = np.abs(specs[0])
                y_mag = np.abs(specs[1])            
                max_mag = np.where(X_mag >= y_mag, X_mag, y_mag)  
                v_spec = specs[1] - max_mag * np.exp(1.j * np.angle(specs[0]))
                update_progress(**progress_kwargs,
                step=(1))
                sf.write(Instrumental_path, spec_utils.cmb_spectrogram_to_wave(-v_spec, mp), mp.param['sr'])
                
                    
                if data['inst_only']:
                    if file_exists_v == 'there':
                        pass
                    else:
                        try:
                            os.remove(vocal_path)
                        except:
                            pass
     
                widget_text.write('Done!\n')
          
        
        if data['saveFormat'] == 'Mp3':
            try:
                if data['inst_only'] == True:
                    pass
                else:
                    musfile = pydub.AudioSegment.from_wav(vocal_path)
                    musfile.export(vocal_path_mp3, format="mp3", bitrate="320k")
                    if file_exists_v == 'there':
                        pass
                    else:
                        try:
                            os.remove(vocal_path)
                        except:
                            pass
                if data['voc_only'] == True:
                    pass
                else:
                    musfile = pydub.AudioSegment.from_wav(Instrumental_path)
                    musfile.export(Instrumental_path_mp3, format="mp3", bitrate="320k")
                    if file_exists_i == 'there':
                        pass
                    else:
                        try:
                            os.remove(Instrumental_path)
                        except:
                            pass
                    if data['non_red'] == True:
                        musfile = pydub.AudioSegment.from_wav(non_reduced_vocal_path)
                        musfile.export(non_reduced_vocal_path_mp3, format="mp3", bitrate="320k") 
                        if file_exists_n == 'there':
                            pass
                        else:
                            try:
                                os.remove(non_reduced_vocal_path)
                            except:
                                pass
                        
            except Exception as e:
                traceback_text = ''.join(traceback.format_tb(e.__traceback__))
                errmessage = f'Traceback Error: "{traceback_text}"\n{type(e).__name__}: "{e}"\n'
                if "ffmpeg" in errmessage:
                    widget_text.write(base_text + 'Failed to save output(s) as Mp3(s).\n')
                    widget_text.write(base_text + 'FFmpeg might be missing or corrupted, please check error log.\n')
                    widget_text.write(base_text + 'Moving on...\n')
                else:
                    widget_text.write(base_text + 'Failed to save output(s) as Mp3(s).\n')
                    widget_text.write(base_text + 'Please check error log.\n')
                    widget_text.write(base_text + 'Moving on...\n')
                try:
                    with open('errorlog.txt', 'w') as f:
                        f.write(f'Last Error Received:\n\n' +
                                f'Error Received while attempting to save file as mp3 "{os.path.basename(music_file)}":\n\n' + 
                                f'Process Method: MDX-Net\n\n' +
                                f'FFmpeg might be missing or corrupted.\n\n' +
                                f'If this error persists, please contact the developers.\n\n' + 
                                f'Raw error details:\n\n' +
                                errmessage + f'\nError Time Stamp: [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
                except:
                    pass
            
        if data['saveFormat'] == 'Flac':
            try:
                if data['inst_only'] == True:
                    pass
                else:
                    musfile = pydub.AudioSegment.from_wav(vocal_path)
                    musfile.export(vocal_path_flac, format="flac") 
                    if file_exists_v == 'there':
                        pass
                    else:
                        try:
                            os.remove(vocal_path)
                        except:
                            pass
                if data['voc_only'] == True:
                    pass
                else:
                    musfile = pydub.AudioSegment.from_wav(Instrumental_path)
                    musfile.export(Instrumental_path_flac, format="flac")  
                    if file_exists_i == 'there':
                        pass
                    else:
                        try:
                            os.remove(Instrumental_path)
                        except:
                            pass  
                    if data['non_red'] == True:
                        musfile = pydub.AudioSegment.from_wav(non_reduced_vocal_path)
                        musfile.export(non_reduced_vocal_path_flac, format="flac") 
                        if file_exists_n == 'there':
                            pass
                        else:
                            try:
                                os.remove(non_reduced_vocal_path)
                            except:
                                pass
                        
            except Exception as e:
                traceback_text = ''.join(traceback.format_tb(e.__traceback__))
                errmessage = f'Traceback Error: "{traceback_text}"\n{type(e).__name__}: "{e}"\n'
                if "ffmpeg" in errmessage:
                    widget_text.write(base_text + 'Failed to save output(s) as Flac(s).\n')
                    widget_text.write(base_text + 'FFmpeg might be missing or corrupted, please check error log.\n')
                    widget_text.write(base_text + 'Moving on...\n')
                else:
                    widget_text.write(base_text + 'Failed to save output(s) as Flac(s).\n')
                    widget_text.write(base_text + 'Please check error log.\n')
                    widget_text.write(base_text + 'Moving on...\n')
                try:
                    with open('errorlog.txt', 'w') as f:
                        f.write(f'Last Error Received:\n\n' +
                                f'Error Received while attempting to save file as flac "{os.path.basename(music_file)}":\n\n' + 
                                f'Process Method: MDX-Net\n\n' +
                                f'FFmpeg might be missing or corrupted.\n\n' +
                                f'If this error persists, please contact the developers.\n\n' + 
                                f'Raw error details:\n\n' +
                                errmessage + f'\nError Time Stamp: [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
                except:
                    pass

        if data['noisereduc_s'] == 'None':
            pass
        elif data['non_red'] == True:
            pass
        elif data['inst_only']:
            if file_exists_n == 'there':
                pass
            else:
                try:
                    os.remove(non_reduced_vocal_path)
                except:
                    pass
        else:
            try:
                os.remove(non_reduced_vocal_path)
            except:
                pass
        
        widget_text.write(base_text + 'Completed Seperation!\n')

    def demix(self, mix):
        # 1 = demucs only
        # 0 = onnx only
        if data['chunks'] == 'Full':
            chunk_set = 0
        else: 
            chunk_set = data['chunks']

        if data['chunks'] == 'Auto':
            if data['gpu'] == 0:
                try:
                    gpu_mem = round(torch.cuda.get_device_properties(0).total_memory/1.074e+9)
                except:
                    widget_text.write(base_text + 'NVIDIA GPU Required for conversion!\n')
                if int(gpu_mem) <= int(6):
                    chunk_set = int(5)
                    widget_text.write(base_text + 'Chunk size auto-set to 5... \n')
                if gpu_mem in [7, 8, 9, 10, 11, 12, 13, 14, 15]:
                    chunk_set = int(10)
                    widget_text.write(base_text + 'Chunk size auto-set to 10... \n')
                if int(gpu_mem) >= int(16):
                    chunk_set = int(40)
                    widget_text.write(base_text + 'Chunk size auto-set to 40... \n')
            if data['gpu'] == -1:
                sys_mem = psutil.virtual_memory().total >> 30
                if int(sys_mem) <= int(4):
                    chunk_set = int(1)
                    widget_text.write(base_text + 'Chunk size auto-set to 1... \n')
                if sys_mem in [5, 6, 7, 8]:
                    chunk_set = int(10)
                    widget_text.write(base_text + 'Chunk size auto-set to 10... \n')
                if sys_mem in [9, 10, 11, 12, 13, 14, 15, 16]:
                    chunk_set = int(25)
                    widget_text.write(base_text + 'Chunk size auto-set to 25... \n')
                if int(sys_mem) >= int(17):
                    chunk_set = int(60)
                    widget_text.write(base_text + 'Chunk size auto-set to 60... \n')
        elif data['chunks'] == 'Full':
            chunk_set = 0
            widget_text.write(base_text + "Chunk size set to full... \n")
        else:
            chunk_set = int(data['chunks'])
            widget_text.write(base_text + "Chunk size user-set to "f"{chunk_set}... \n")
            
        samples = mix.shape[-1]
        margin = margin_set
        chunk_size = chunk_set*44100
        assert not margin == 0, 'margin cannot be zero!'
        if margin > chunk_size:
            margin = chunk_size

        b = np.array([[[0.5]], [[0.5]], [[0.7]], [[0.9]]])
        segmented_mix = {}
        
        if chunk_set == 0 or samples < chunk_size:
            chunk_size = samples
        
        counter = -1
        for skip in range(0, samples, chunk_size):
            counter+=1
    
            s_margin = 0 if counter == 0 else margin
            end = min(skip+chunk_size+margin, samples)

            start = skip-s_margin

            segmented_mix[skip] = mix[:,start:end].copy()
            if end == samples:
                break
  
        
        if not data['demucsmodel']:
            sources = self.demix_base(segmented_mix, margin_size=margin)
        elif data['demucs_only']:
            if split_mode == True:
                sources = self.demix_demucs_split(mix)
            if split_mode == False:
                sources = self.demix_demucs(segmented_mix, margin_size=margin)
        else: # both, apply spec effects
            base_out = self.demix_base(segmented_mix, margin_size=margin)
            print(split_mode)
            if split_mode == True:
                demucs_out = self.demix_demucs_split(mix)
            if split_mode == False:
                demucs_out = self.demix_demucs(segmented_mix, margin_size=margin)
            nan_count = np.count_nonzero(np.isnan(demucs_out)) + np.count_nonzero(np.isnan(base_out))
            if nan_count > 0:
                print('Warning: there are {} nan values in the array(s).'.format(nan_count))
                demucs_out, base_out = np.nan_to_num(demucs_out), np.nan_to_num(base_out)
            sources = {}
            print(data['mixing'])
            
            if 'UVR' in demucs_model_set:
                sources[source_val] = (spec_effects(wave=[demucs_out[1],base_out[0]],
                                            algorithm=data['mixing'],
                                            value=b[source_val])*float(data['compensate'])) # compensation
            else:
                sources[source_val] = (spec_effects(wave=[demucs_out[source_val],base_out[0]],
                                            algorithm=data['mixing'],
                                            value=b[source_val])*float(data['compensate'])) # compensation
        return sources
    
    def demix_base(self, mixes, margin_size):
        chunked_sources = []
        onnxitera = len(mixes)
        onnxitera_calc = onnxitera * 2
        gui_progress_bar_onnx = 0
        widget_text.write(base_text + "Running ONNX Inference...\n")
        widget_text.write(base_text + "Processing "f"{onnxitera} slices... ")
        print(' Running ONNX Inference...')

        for mix in mixes:
            gui_progress_bar_onnx += 1
            if data['demucsmodel']:
                update_progress(**progress_kwargs,
                    step=(0.1 + (0.5/onnxitera_calc * gui_progress_bar_onnx)))
            else:
                update_progress(**progress_kwargs,
                    step=(0.1 + (0.9/onnxitera * gui_progress_bar_onnx)))
 
            cmix = mixes[mix]
            sources = []
            n_sample = cmix.shape[1]
            
            mod = 0 
            for model in self.models:
                mod += 1
                trim = model.n_fft//2
                gen_size = model.chunk_size-2*trim
                pad = gen_size - n_sample%gen_size
                mix_p = np.concatenate((np.zeros((2,trim)), cmix, np.zeros((2,pad)), np.zeros((2,trim))), 1)
                mix_waves = []
                i = 0
                while i < n_sample + pad:
                    waves = np.array(mix_p[:, i:i+model.chunk_size])
                    mix_waves.append(waves)
                    i += gen_size
                mix_waves = torch.tensor(mix_waves, dtype=torch.float32).to(cpu)
                with torch.no_grad():
                    _ort = self.onnx_models[mod]
                    spek = model.stft(mix_waves)
                    
                    tar_waves = model.istft(torch.tensor(_ort.run(None, {'input': spek.cpu().numpy()})[0]))#.cpu()

                    tar_signal = tar_waves[:,:,trim:-trim].transpose(0,1).reshape(2, -1).numpy()[:, :-pad]

                    start = 0 if mix == 0 else margin_size
                    end = None if mix == list(mixes.keys())[::-1][0] else -margin_size
                    if margin_size == 0:
                        end = None
                    sources.append(tar_signal[:,start:end])

            chunked_sources.append(sources)
        _sources = np.concatenate(chunked_sources, axis=-1)
        del self.onnx_models
        widget_text.write('Done!\n')
        return _sources
    
    def demix_demucs(self, mix, margin_size):
        print('shift_set ', shift_set)
        processed = {}
        demucsitera = len(mix)
        demucsitera_calc = demucsitera * 2
        gui_progress_bar_demucs = 0
        widget_text.write(base_text + "Split Mode is off. (Chunks enabled for Demucs Model)\n")
        widget_text.write(base_text + "Running Demucs Inference...\n")
        widget_text.write(base_text + "Processing "f"{len(mix)} slices... ")
        print(' Running Demucs Inference...')
        for nmix in mix:
            gui_progress_bar_demucs += 1
            update_progress(**progress_kwargs,
                step=(0.35 + (1.05/demucsitera_calc * gui_progress_bar_demucs)))
            cmix = mix[nmix]
            cmix = torch.tensor(cmix, dtype=torch.float32)
            ref = cmix.mean(0)        
            cmix = (cmix - ref.mean()) / ref.std()
            with torch.no_grad():
                print(split_mode)
                sources = apply_model(self.demucs, cmix[None], split=split_mode, device=device, overlap=overlap_set, shifts=shift_set, progress=False)[0]
            sources = (sources * ref.std() + ref.mean()).cpu().numpy()
            sources[[0,1]] = sources[[1,0]]

            start = 0 if nmix == 0 else margin_size
            end = None if nmix == list(mix.keys())[::-1][0] else -margin_size
            if margin_size == 0:
                end = None
            processed[nmix] = sources[:,:,start:end].copy()

        sources = list(processed.values())
        sources = np.concatenate(sources, axis=-1)
        widget_text.write('Done!\n')
        return sources
    
    def demix_demucs_split(self, mix):

        print('shift_set ', shift_set)
        widget_text.write(base_text + "Split Mode is on. (Chunks disabled for Demucs Model)\n")
        widget_text.write(base_text + "Running Demucs Inference...\n")
        widget_text.write(base_text + "Processing "f"{len(mix)} slices... ")
        print(' Running Demucs Inference...')
          
        mix = torch.tensor(mix, dtype=torch.float32)
        ref = mix.mean(0)        
        mix = (mix - ref.mean()) / ref.std()
        
        with torch.no_grad():
            sources = apply_model(self.demucs, mix[None], split=split_mode, device=device, overlap=overlap_set, shifts=shift_set, progress=False)[0]
            
        widget_text.write('Done!\n')
            
        sources = (sources * ref.std() + ref.mean()).cpu().numpy()
        sources[[0,1]] = sources[[1,0]]
        return sources
        
data = {
    # Paths
    'input_paths': None,
    'export_path': None,
    'saveFormat': 'Wav',
    # Processing Options
    'demucsmodel': True,
    'gpu': -1,
    'chunks': 10,
    'non_red': False,
    'noisereduc_s': 3,
    'modelFolder': False,
    'voc_only': False,
    'inst_only': False,
    'n_fft_scale': 6144,
    'dim_f': 2048,
    'noise_pro_select': 'Auto Select',
    'overlap': 0.5,
    'shifts': 0,
    'margin': 44100,
    'split_mode': False,
    'compensate': 1.03597672895,
    'demucs_only': False,
    'mixing': 'Default',
    'DemucsModel_MDX': 'UVR_Demucs_Model_1',
    # Choose Model
    'mdxnetModel': 'UVR-MDX-NET 1',
    'mdxnetModeltype': 'Vocals (Custom)',
}
default_chunks = data['chunks']
default_noisereduc_s = data['noisereduc_s']

def update_progress(progress_var, total_files, file_num, step: float = 1):
    """Calculate the progress for the progress widget in the GUI"""
    base = (100 / total_files)
    progress = base * (file_num - 1)
    progress += base * step

    progress_var.set(progress)

def get_baseText(total_files, file_num):
    """Create the base text for the command widget"""
    text = 'File {file_num}/{total_files} '.format(file_num=file_num,
                                                total_files=total_files)
    return text

warnings.filterwarnings("ignore")
cpu = torch.device('cpu')

def hide_opt():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def main(window: tk.Wm, text_widget: tk.Text, button_widget: tk.Button, progress_var: tk.Variable,
         **kwargs: dict):

    global widget_text
    global gui_progress_bar
    global music_file
    global default_chunks
    global default_noisereduc_s
    global _basename
    global _mixture
    global modeltype
    global n_fft_scale_set
    global dim_f_set
    global progress_kwargs
    global base_text
    global model_set
    global model_set_name
    global stemset_n
    global noise_pro_set
    global demucs_model_set

    global mdx_model_hash
    
    global channel_set
    global margin_set
    global overlap_set
    global shift_set
    global source_val
    global split_mode
    
    global demucs_switch
    
    # Update default settings
    default_chunks = data['chunks']
    default_noisereduc_s = data['noisereduc_s']
    
    widget_text = text_widget
    gui_progress_bar = progress_var
    
    #Error Handling
    
    onnxmissing = "[ONNXRuntimeError] : 3 : NO_SUCHFILE"
    onnxmemerror = "onnxruntime::CudaCall CUDA failure 2: out of memory"
    onnxmemerror2 = "onnxruntime::BFCArena::AllocateRawInternal"
    systemmemerr = "DefaultCPUAllocator: not enough memory"
    runtimeerr = "CUDNN error executing cudnnSetTensorNdDescriptor"
    cuda_err = "CUDA out of memory"
    mod_err = "ModuleNotFoundError"
    file_err = "FileNotFoundError"
    ffmp_err = """audioread\__init__.py", line 116, in audio_open"""
    sf_write_err = "sf.write"
    model_adv_set_err = "Got invalid dimensions for input"
    
    try:
        with open('errorlog.txt', 'w') as f:
            f.write(f'No errors to report at this time.' + f'\n\nLast Process Method Used: MDX-Net' +
                    f'\nLast Conversion Time Stamp: [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
    except:
        pass
    
    data.update(kwargs)
    
    if data['mdxnetModeltype'] == 'Vocals (Custom)':
        stemset = 'v'
        source_val_set = 3
        stem_name = '(Vocals)'
    if data['mdxnetModeltype'] == 'Other (Custom)':
        stemset = 'o'
        source_val_set = 2
        stem_name = '(Other)'
    if data['mdxnetModeltype'] == 'Drums (Custom)':
        stemset = 'd'
        source_val_set = 1
        stem_name = '(Drums)'
    if data['mdxnetModeltype'] == 'Bass (Custom)':
        stemset = 'b'
        source_val_set = 0
        stem_name = '(Bass)'
    if data['mdxnetModeltype'] == 'Vocals (Default)':
        stemset = 'v'
        source_val_set = 3
        stem_name = '(Vocals)'
    if data['mdxnetModeltype'] == 'Other (Default)':
        stemset = 'o'
        source_val_set = 2
        stem_name = '(Other)'
    if data['mdxnetModeltype'] == 'Drums (Default)':
        stemset = 'd'
        source_val_set = 1
        stem_name = '(Drums)'
    if data['mdxnetModeltype'] == 'Bass (Default)':
        stemset = 'b'
        source_val_set = 0
        stem_name = '(Bass)'
        
    if data['mdxnetModel'] == 'UVR-MDX-NET 1':
        if os.path.isfile('models/MDX_Net_Models/UVR_MDXNET_1_9703.onnx'):
            model_set = 'UVR_MDXNET_1_9703'
            model_set_name = 'UVR_MDXNET_1_9703'
        else:
            model_set = 'UVR_MDXNET_9703'
            model_set_name = 'UVR_MDXNET_9703'
        modeltype = 'v'
        noise_pro = 'MDX-NET_Noise_Profile_14_kHz'
        stemset_n = '(Vocals)'
        source_val = 3
        n_fft_scale_set=6144 
        dim_f_set=2048
    elif data['mdxnetModel'] == 'UVR-MDX-NET 2':
        if os.path.isfile('models/MDX_Net_Models/UVR_MDXNET_2_9682.onnx'):
            model_set = 'UVR_MDXNET_2_9682'
            model_set_name = 'UVR_MDXNET_2_9682'
        else:
            model_set = 'UVR_MDXNET_9682'
            model_set_name = 'UVR_MDXNET_9682'
        modeltype = 'v'
        noise_pro = 'MDX-NET_Noise_Profile_14_kHz'
        stemset_n = '(Vocals)'
        source_val = 3
        n_fft_scale_set=6144 
        dim_f_set=2048
    elif data['mdxnetModel'] == 'UVR-MDX-NET 3':
        if os.path.isfile('models/MDX_Net_Models/UVR_MDXNET_3_9662.onnx'):
            model_set = 'UVR_MDXNET_3_9662'
            model_set_name = 'UVR_MDXNET_3_9662'
        else:
            model_set = 'UVR_MDXNET_9662'
            model_set_name = 'UVR_MDXNET_9662'
        modeltype = 'v'
        noise_pro = 'MDX-NET_Noise_Profile_14_kHz'
        stemset_n = '(Vocals)'
        source_val = 3
        n_fft_scale_set=6144 
        dim_f_set=2048
    elif data['mdxnetModel'] == 'UVR-MDX-NET Karaoke':
        model_set = 'UVR_MDXNET_KARA'
        model_set_name = 'UVR_MDXNET_Karaoke'
        modeltype = 'v'
        noise_pro = 'MDX-NET_Noise_Profile_14_kHz'
        stemset_n = '(Vocals)'
        source_val = 3
        n_fft_scale_set=6144 
        dim_f_set=2048
    elif 'other' in data['mdxnetModel']:
        model_set = 'other'
        model_set_name = 'other'
        modeltype = 'o'
        noise_pro = 'MDX-NET_Noise_Profile_Full_Band'
        stemset_n = '(Other)'
        source_val = 2
        n_fft_scale_set=8192 
        dim_f_set=2048
    elif 'drums' in data['mdxnetModel']:
        model_set = 'drums'
        model_set_name = 'drums'
        modeltype = 'd'
        noise_pro = 'MDX-NET_Noise_Profile_Full_Band'
        stemset_n = '(Drums)'
        source_val = 1
        n_fft_scale_set=4096 
        dim_f_set=2048
    elif 'bass' in data['mdxnetModel']:
        model_set = 'bass'
        model_set_name = 'bass'
        modeltype = 'b'
        noise_pro = 'MDX-NET_Noise_Profile_Full_Band'
        stemset_n = '(Bass)'
        source_val = 0
        n_fft_scale_set=16384 
        dim_f_set=2048
    else:
        model_set = data['mdxnetModel']
        model_set_name = data['mdxnetModel']
        modeltype = stemset
        noise_pro = 'MDX-NET_Noise_Profile_Full_Band'
        stemset_n = stem_name
        source_val = source_val_set
        n_fft_scale_set=int(data['n_fft_scale'])
        dim_f_set=int(data['dim_f'])
        
        
    if data['noise_pro_select'] == 'Auto Select':
        noise_pro_set = noise_pro
    else:
        noise_pro_set = data['noise_pro_select']
        

    print(n_fft_scale_set)
    print(dim_f_set)
    print(data['DemucsModel_MDX'])
    

    stime = time.perf_counter()
    progress_var.set(0)
    text_widget.clear()
    button_widget.configure(state=tk.DISABLED)  # Disable Button

    try:    #Load File(s)
        for file_num, music_file in tqdm(enumerate(data['input_paths'], start=1)):

            overlap_set = float(data['overlap'])
            channel_set = int(data['channel'])
            margin_set = int(data['margin'])
            shift_set = int(data['shifts'])
            demucs_model_set = data['DemucsModel_MDX']
            split_mode = data['split_mode']
            demucs_switch = data['demucsmodel']
            
            if stemset_n == '(Bass)':
                if 'UVR' in demucs_model_set:
                    text_widget.write('The selected Demucs model can only be used with vocal stems.\n')
                    text_widget.write('Please select a 4 stem Demucs model and try again.\n\n')
                    text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
                    progress_var.set(0)
                    button_widget.configure(state=tk.NORMAL)  # Enable Button
                    return 
                else:
                    pass
            if stemset_n == '(Drums)':
                if 'UVR' in demucs_model_set:
                    text_widget.write('The selected Demucs model can only be used with vocal stems.\n')
                    text_widget.write('Please select a 4 stem Demucs model and try again.\n\n')
                    text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
                    progress_var.set(0)
                    button_widget.configure(state=tk.NORMAL)  # Enable Button
                    return 
                else:
                    pass
            if stemset_n == '(Other)':
                if 'UVR' in demucs_model_set:
                    text_widget.write('The selected Demucs model can only be used with vocal stems.\n')
                    text_widget.write('Please select a 4 stem Demucs model and try again.\n\n')
                    text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
                    progress_var.set(0)
                    button_widget.configure(state=tk.NORMAL)  # Enable Button
                    return 
                else:
                    pass

            _mixture = f'{data["input_paths"]}'
            _basename = f'{data["export_path"]}/{file_num}_{os.path.splitext(os.path.basename(music_file))[0]}'
                
            # -Get text and update progress-
            base_text = get_baseText(total_files=len(data['input_paths']),
                                        file_num=file_num)
            progress_kwargs = {'progress_var': progress_var,
                            'total_files': len(data['input_paths']),
                            'file_num': file_num}
            
            print(model_set)
            
            try:
                
                if float(data['noisereduc_s']) >= 10:
                    text_widget.write('Error: Noise Reduction only supports values between 0-10.\nPlease set a value between 0-10 (with or without decimals) and try again.')
                    progress_var.set(0)
                    button_widget.configure(state=tk.NORMAL)  # Enable Button
                    return
                
                total, used, free = shutil.disk_usage("/") 
                
                    
                total_space = int(total/1.074e+9)
                used_space = int(used/1.074e+9)
                free_space = int(free/1.074e+9)
                
                    
                if int(free/1.074e+9) <= int(2):
                    text_widget.write('Error: Not enough storage on main drive to continue. Your main drive must have \nat least 3 GB\'s of storage in order for this application function properly. \n\nPlease ensure your main drive has at least 3 GB\'s of storage and try again.\n\n')
                    text_widget.write('Detected Total Space: ' + str(total_space) + ' GB' + '\n')
                    text_widget.write('Detected Used Space: ' + str(used_space) + ' GB' + '\n')
                    text_widget.write('Detected Free Space: ' + str(free_space) + ' GB' + '\n')
                    progress_var.set(0)
                    button_widget.configure(state=tk.NORMAL)  # Enable Button
                    return 
                
                if int(free/1.074e+9) in [3, 4, 5, 6, 7, 8]:
                    text_widget.write('Warning: Your main drive is running low on storage. Your main drive must have \nat least 3 GB\'s of storage in order for this application function properly.\n\n')
                    text_widget.write('Detected Total Space: ' + str(total_space) + ' GB' + '\n')
                    text_widget.write('Detected Used Space: ' + str(used_space) + ' GB' + '\n')
                    text_widget.write('Detected Free Space: ' + str(free_space) + ' GB' + '\n\n')
            except:
                pass
            
            if data['noisereduc_s'] == 'None':
                pass
            else:
                if not os.path.isfile("lib_v5\sox\sox.exe"):
                    data['noisereduc_s'] = 'None'
                    data['non_red'] = False
                    widget_text.write(base_text + 'SoX is missing and required for noise reduction.\n')
                    widget_text.write(base_text + 'See the \"More Info\" tab in the Help Guide.\n')
                    widget_text.write(base_text + 'Noise Reduction will be disabled until SoX is available.\n\n')
        
            update_progress(**progress_kwargs,
                            step=0)       
            
            e = os.path.join(data["export_path"])
            
            demucsmodel = 'models/Demucs_Models/' + str(data['DemucsModel_MDX'])

            pred = Predictor()
            pred.prediction_setup()
            
            print(demucsmodel)
            
            # split
            pred.prediction(
                m=music_file,
            )
            
    except Exception as e:
        traceback_text = ''.join(traceback.format_tb(e.__traceback__))
        message = f'Traceback Error: "{traceback_text}"\n{type(e).__name__}: "{e}"\n'
        if runtimeerr in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'Your PC cannot process this audio file with the chunk size selected.\nPlease lower the chunk size and try again.\n\n')
            text_widget.write(f'If this error persists, please contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'Your PC cannot process this audio file with the chunk size selected.\nPlease lower the chunk size and try again.\n\n' +
                            f'If this error persists, please contact the developers.\n\n' + 
                            f'Raw error details:\n\n' +
                            message + f'\nError Time Stamp: [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if cuda_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The application was unable to allocate enough GPU memory to use this model.\n')
            text_widget.write(f'Please close any GPU intensive applications and try again.\n')
            text_widget.write(f'If the error persists, your GPU might not be supported.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The application was unable to allocate enough GPU memory to use this model.\n' + 
                            f'Please close any GPU intensive applications and try again.\n' + 
                            f'If the error persists, your GPU might not be supported.\n\n' + 
                            f'Raw error details:\n\n' +
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return
        
        if mod_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'Application files(s) are missing.\n')
            text_widget.write("\n" + f'{type(e).__name__} - "{e}"' + "\n\n")
            text_widget.write(f'Please check for missing files/scripts in the app directory and try again.\n')
            text_widget.write(f'If the error persists, please reinstall application or contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'Application files(s) are missing.\n' + 
                            f'Please check for missing files/scripts in the app directory and try again.\n' + 
                            f'If the error persists, please reinstall application or contact the developers.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if file_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'Missing file error raised.\n')
            text_widget.write("\n" + f'{type(e).__name__} - "{e}"' + "\n\n")
            text_widget.write("\n" + f'Please address the error and try again.' + "\n")
            text_widget.write(f'If this error persists, please contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            torch.cuda.empty_cache()
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'Missing file error raised.\n' + 
                            "\n" + f'Please address the error and try again.' + "\n" +
                            f'If this error persists, please contact the developers.\n\n' +
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if ffmp_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The input file type is not supported or FFmpeg is missing.\n')
            text_widget.write(f'Please select a file type supported by FFmpeg and try again.\n\n')
            text_widget.write(f'If FFmpeg is missing or not installed, you will only be able to process \".wav\" files \nuntil it is available on this system.\n\n')
            text_widget.write(f'See the \"More Info\" tab in the Help Guide.\n\n')
            text_widget.write(f'If this error persists, please contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            torch.cuda.empty_cache()
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The input file type is not supported or FFmpeg is missing.\nPlease select a file type supported by FFmpeg and try again.\n\n' + 
                            f'If FFmpeg is missing or not installed, you will only be able to process \".wav\" files until it is available on this system.\n\n' + 
                            f'See the \"More Info\" tab in the Help Guide.\n\n' + 
                            f'If this error persists, please contact the developers.\n\n' +
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if onnxmissing in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The application could not detect this MDX-Net model on your system.\n')
            text_widget.write(f'Please make sure all the models are present in the correct directory.\n')
            text_widget.write(f'If the error persists, please reinstall application or contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The application could not detect this MDX-Net model on your system.\n' + 
                            f'Please make sure all the models are present in the correct directory.\n' + 
                            f'If the error persists, please reinstall application or contact the developers.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if onnxmemerror in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The application was unable to allocate enough GPU memory to use this model.\n')
            text_widget.write(f'Please do the following:\n\n1. Close any GPU intensive applications.\n2. Lower the set chunk size.\n3. Then try again.\n\n')
            text_widget.write(f'If the error persists, your GPU might not be supported.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The application was unable to allocate enough GPU memory to use this model.\n' + 
                            f'Please do the following:\n\n1. Close any GPU intensive applications.\n2. Lower the set chunk size.\n3. Then try again.\n\n' + 
                            f'If the error persists, your GPU might not be supported.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if onnxmemerror2 in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The application was unable to allocate enough GPU memory to use this model.\n')
            text_widget.write(f'Please do the following:\n\n1. Close any GPU intensive applications.\n2. Lower the set chunk size.\n3. Then try again.\n\n')
            text_widget.write(f'If the error persists, your GPU might not be supported.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The application was unable to allocate enough GPU memory to use this model.\n' + 
                            f'Please do the following:\n\n1. Close any GPU intensive applications.\n2. Lower the set chunk size.\n3. Then try again.\n\n' + 
                            f'If the error persists, your GPU might not be supported.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if sf_write_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'Could not write audio file.\n')
            text_widget.write(f'This could be due to low storage on target device or a system permissions issue.\n')
            text_widget.write(f"\nFor raw error details, go to the Error Log tab in the Help Guide.\n")
            text_widget.write(f'\nIf the error persists, please contact the developers.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'Could not write audio file.\n' + 
                            f'This could be due to low storage on target device or a system permissions issue.\n' + 
                            f'If the error persists, please contact the developers.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if systemmemerr in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The application was unable to allocate enough system memory to use this \nmodel.\n\n')
            text_widget.write(f'Please do the following:\n\n1. Restart this application.\n2. Ensure any CPU intensive applications are closed.\n3. Then try again.\n\n')
            text_widget.write(f'Please Note: Intel Pentium and Intel Celeron processors do not work well with \nthis application.\n\n')
            text_widget.write(f'If the error persists, the system may not have enough RAM, or your CPU might \nnot be supported.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The application was unable to allocate enough system memory to use this model.\n' + 
                            f'Please do the following:\n\n1. Restart this application.\n2. Ensure any CPU intensive applications are closed.\n3. Then try again.\n\n' + 
                            f'Please Note: Intel Pentium and Intel Celeron processors do not work well with this application.\n\n' +
                            f'If the error persists, the system may not have enough RAM, or your CPU might \nnot be supported.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        if model_adv_set_err in message:
            text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
            text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
            text_widget.write(f'\nError Received:\n\n')
            text_widget.write(f'The current ONNX model settings are not compatible with the selected \nmodel.\n\n')
            text_widget.write(f'Please re-configure the advanced ONNX model settings accordingly and try \nagain.\n\n')
            text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
            try:
                with open('errorlog.txt', 'w') as f:
                    f.write(f'Last Error Received:\n\n' +
                            f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                            f'Process Method: MDX-Net\n\n' +
                            f'The current ONNX model settings are not compatible with the selected model.\n\n' + 
                            f'Please re-configure the advanced ONNX model settings accordingly and try again.\n\n' + 
                            message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
            except:
                pass
            torch.cuda.empty_cache()
            progress_var.set(0)
            button_widget.configure(state=tk.NORMAL)  # Enable Button
            return 
        
        
        print(traceback_text)
        print(type(e).__name__, e)
        print(message)
        
        try:
            with open('errorlog.txt', 'w') as f:
                f.write(f'Last Error Received:\n\n' +
                        f'Error Received while processing "{os.path.basename(music_file)}":\n' + 
                        f'Process Method: MDX-Net\n\n' +
                        f'If this error persists, please contact the developers with the error details.\n\n' +
                        message + f'\nError Time Stamp [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]\n') 
        except:
            tk.messagebox.showerror(master=window,
                            title='Error Details',
                            message=message)
        progress_var.set(0)
        text_widget.write("\n" + base_text + f'Separation failed for the following audio file:\n')
        text_widget.write(base_text + f'"{os.path.basename(music_file)}"\n')
        text_widget.write(f'\nError Received:\n')
        text_widget.write("\nFor raw error details, go to the Error Log tab in the Help Guide.\n")
        text_widget.write("\n" + f'Please address the error and try again.' + "\n")
        text_widget.write(f'If this error persists, please contact the developers with the error details.\n\n')
        text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')
        try:
            torch.cuda.empty_cache()
        except:
            pass
        button_widget.configure(state=tk.NORMAL)  # Enable Button
        return
    
    progress_var.set(0)

    text_widget.write(f'\nConversion(s) Completed!\n')
        
    text_widget.write(f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}')  # nopep8
    torch.cuda.empty_cache() 
    button_widget.configure(state=tk.NORMAL)  # Enable Button
    
if __name__ == '__main__':
    start_time = time.time()
    main()
    print("Successfully completed music demixing.");print('Total time: {0:.{1}f}s'.format(time.time() - start_time, 1))

