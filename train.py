from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import pandas as pd
import torchaudio
import torch
import torchaudio.transforms as T
import torch.nn as nn

from model import AudioCNN

class ESC50Dataset(Dataset):
    def __init__(self, data_dir, metadata_file, split='train', transform=None):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.metadata = pd.read_csv(metadata_file)
        self.split = split
        self.transform = transform
        
        if split == 'train':
            self.metadata = self.metadata[self.metadata['fold'] != 5]
        else:
            self.metadata = self.metadata[self.metadata['fold'] == 5]
            
        self.classes = sorted(self.metadata['category'].unique())
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.metadata['label'] = self.metadata['category'].map(self.class_to_idx)
        
    def __len__(self):
        return len(self.metadata)
    
    def __getitem__(self, index):
        row  = self.metadata.iloc[index]
        audio_path = self.data_dir / "audio" / row['filename']
        
        waveform, sample_rate = torchaudio.load(audio_path)
        
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
            
        if self.transform:
            spectrogram = self.transform(waveform)
        else:
            spectrogram = waveform
            
        return spectrogram, row['label']
    
    
def train():
    esc50_dir = "data"
    
    train_transform = nn.Sequential(
        T.MelSpectrogram(sample_rate=22050,
                            n_mels=128,
                            n_fft=1024,
                            hop_length=512,
                            f_min=0,
                            f_max=11025
        ),
        T.AmplitudeToDB(),
        T.FrequencyMasking(freq_mask_param=30),
        T.TimeMasking(time_mask_param=80)
    )
    
    val_transform = nn.Sequential(
        T.MelSpectrogram(sample_rate=22050,
                            n_mels=128,
                            n_fft=1024,
                            hop_length=512,
                            f_min=0,
                            f_max=11025
        ),
        T.AmplitudeToDB()
    )
    
    train_dataset = ESC50Dataset(data_dir=esc50_dir, metadata_file=esc50_dir + "/meta/esc50.csv", split='train', transform=train_transform)
    val_dataset = ESC50Dataset(data_dir=esc50_dir, metadata_file=esc50_dir + "/meta/esc50.csv", split='val', transform=val_transform)
    
    print(f"Number of training samples: {len(train_dataset)}")
    print(f"Number of validation samples: {len(val_dataset)}")
    
    train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = AudioCNN(num_classes=len(train_dataset.classes))
    model.to(device)
    
    num_epochs = 100
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    
