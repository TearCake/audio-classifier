import torch.nn as nn
import torchaudio.transforms as T
import torch
import base64
from pydantic import BaseModel
import soundfile as sf
from model import AudioCNN
import io
import numpy as np
import librosa

class AudioProcessor:
    def __init__(self):
        self.transform = nn.Sequential(
            T.MelSpectrogram(
                sample_rate=44100,
                n_fft=1024,
                hop_length=512,
                n_mels=128,
                f_min=0,
                f_max=11025
            ),
            T.AmplitudeToDB()
        )
        
    def process_audio_chunk(self, audio_data):
        waveform = torch.from_numpy(audio_data).float()
        
        waveform = waveform.unsqueeze(0) 
        
        spectogram = self.transform(waveform)
        
        return spectogram.unsqueeze(0)
    
class InferenceRequest(BaseModel):
    audio_data: str
    
class AudioClassifier:
    def load_model(self):
        print("Loading model...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        checkpoint = torch.load(
            "models/checkpoints/best_model.pth", 
            map_location=self.device
        )
        self.classes = checkpoint['classes']
        
        self.model = AudioCNN(num_classes=len(self.classes))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        self.audio_processor = AudioProcessor()
        print("Model loaded successfully.")
        
    def inference(self, request: InferenceRequest):
        audio_bytes = base64.b64decode(request.audio_data)
        
        audio_data, sample_rate = sf.read(
            io.BytesIO(audio_bytes), 
            dtype='float32'
        )
        
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
            
        if sample_rate != 44100:
            audio_data = librosa.resample(
                y=audio_data, 
                orig_sr=sample_rate, 
                target_sr=44100
            )
            
        spectrogram = self.audio_processor.process_audio_chunk(audio_data)
        spectrogram = spectrogram.to(self.device)
        
        with torch.no_grad():
            output, feature_maps = self.model(spectrogram, return_feature_maps=True)
            
            output = torch.nan_to_num(output)
            probabilities = torch.softmax(output, dim=1) #dim=0 for batch, 1 for classes
            top3_prob, top3_idx = torch.topk(probabilities[0], k=3)
            
            
            predictions = [{"class": self.classes[idx.item()], "confidence": prob.item()} 
                            for prob, idx in zip(top3_prob, top3_idx)]
            
            viz_data = {}
            for name, tensor in feature_maps.items():
                if tensor.ndim == 4: # batch_size, channels, height, width
                    aggreagted_tensor = torch.mean(tensor, dim=1)
                    squeezed_tensor = aggreagted_tensor.squeeze(0)
                    numpy_array = squeezed_tensor.cpu().numpy()
                    clean_array = np.nan_to_num(numpy_array)
                    viz_data[name] = {
                        "shape": list(clean_array.shape),
                        "values": clean_array.tolist()
                    }
            
            spectogram_np = spectrogram.squeeze(0).squeeze(0).cpu().numpy()
            clean_spectrogram = np.nan_to_num(spectogram_np)
            
            max_samples = 8000
            if len(audio_data) > max_samples:
                step = len(audio_data) // max_samples
                waveform_data = audio_data[::step]
            else:
                waveform_data = audio_data
            
        response = {
            "predictions": predictions,
            "visualization": viz_data,
            "input_spectrogram": {
                "shape": list(clean_spectrogram.shape),
                "values": clean_spectrogram.tolist()
            },
            "waveform": {
                "values": waveform_data.tolist(),
                "sample_rate": 44100,
                "duration": len(audio_data) / 44100
            }
        }
        
        return response
    
def main():
    audio_data, sample_rate = sf.read("cock.wav")
    
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    audio_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    payload = {"audio_data": audio_b64}
    
    server = AudioClassifier()
    server.load_model()
    result = server.inference(InferenceRequest(**payload))
    
    waveform_info = result.get("waveform", {})
    if waveform_info:
        values = waveform_info.get("values", [])
        print(f"First 10 values: {[round(v, 4) for v in values[:10]]}...")
        print(f"Duration: {waveform_info.get('duration', 0):.2f} seconds")
    
    print("Top 3 Predictions:")
    for pred in result.get("predictions", []):
        print(f"  {pred['class']}: {pred['confidence']:.2f}%")


if __name__ == "__main__":
    main()