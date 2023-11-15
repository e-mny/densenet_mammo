import pandas as pd
import os
from torch.utils.data import Dataset, random_split
import pydicom
import numpy as np
from PIL import Image
import torch
import cv2
import random
from utils.config import VAL_RATIO


class CustomImageDataset(Dataset):
    def __init__(self, directory, form = 'calc', mode = 'train', transform = None, train = True):
        self.directory = directory
        self.form = form
        self.train = train
        self.mode = mode
        self.val_ratio = VAL_RATIO
        if self.mode == "train":
            self.df_dir = os.path.join(self.directory, "train.csv")
        elif self.mode == "val":
            self.df_dir = os.path.join(self.directory, "val.csv")
        elif self.mode == "test":
            self.df_dir = os.path.join(self.directory, "test.csv")
        else:
            self.df_dir = os.path.join(self.directory, "combined_data.csv")
        self.data = []
        self.labels = []
        self.transform = transform
       
        # Create a CLAHE object (Contrast Limited Adaptive Histogram Equalization)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        try:
            # Load and preprocess data sample at index idx
            image_path = self.data[idx]
            label = self.labels[idx]
            
            
            # Dicom
            # image_path = os.path.join(self.directory, self.mode, str(idx + 1), "1-1.dcm")
            # imageArr = self.load_dicom(image_path)
            
            # JPEG
            imageArr = self.load_jpeg(image_path)

            if self.transform:
                imageArr = self.transform(imageArr)

            return imageArr, label
        except IndexError:
                print(f"Index out of range: {idx}")
                return None
    
    def getLabel(self, label_text):
        label_text = label_text.lower()
        if "malignant" in label_text:
            return 1
        else:
            return 0
    
    def load_dicom(self, dicom_path):
        ds = pydicom.dcmread(dicom_path)
        image = ds.pixel_array

        # Convert to 8-bit grayscale
        image = image - np.min(image)
        image = (image / np.max(image) * 255).astype(np.uint8)

        imagearray = Image.fromarray(image.astype(float))
        return imagearray
    
    def load_jpeg(self, jpeg_path):
        image = Image.open(jpeg_path).convert("RGB")
        return image
    
    def apply_clahe(self, image):
        # Apply CLAHE to the image
        clahe_image = self.clahe.apply(image)
        return clahe_image

    def apply_mean_filter(self, image):
        return cv2.blur(image, (5, 5))

    def apply_gaussian_filter(self, image):
        return cv2.GaussianBlur(image, (5, 5), 0)

    def apply_median_filter(self, image):
        return cv2.medianBlur(image, 5)
    
    def apply_combined_filter(self, image):
        return cv2.addWeighted(self.apply_mean_filter(image), 0.5, self.apply_median_filter(image), 0.5, 0)
    
    def toPILImage(self, image):
        return Image.fromarray(image)
    
    def stack_jpeg(self, image):
        stacked_image = np.stack((image,) * 3, axis=-1)
        return stacked_image
    
    def preprocessFile(self, boolean):
        if boolean:
            return "1-1_preprocessed.png"
        else:
            return "1-1.png"
        
    def generateTrainValSplit(self):
        random.seed(42) # Set seed num for reproducibility of splitting images from training data into training and validation sets
        
        # Generate random indices for the training set
        train_indices_list = sorted(random.sample(range(self.df_len), int((1 - self.val_ratio) * self.df_len)))
        # Define the validation indices by excluding the training indices
        val_indices_list = [idx for idx in range(self.df_len) if idx not in train_indices_list]
        if self.train:
            return train_indices_list
        else:
            return val_indices_list
        
class CBISDataset(CustomImageDataset):
    """
    {
        Directory: Where data is stored,
        Form: 'calc' or 'mass',
        Mode: 'train' or 'test',
        Transform: For Data Augmentation Compose object,
        Train: Boolean value for whether it is the training or validation set
        True -> Training
        False -> Validation
        Preprocess: Boolean value for choosing preprocessed image or not
        ROI: Boolean value for choosing ROI images or not
    }
    """
    
    def __init__(self, directory = "/home/emok/sq58_scratch/emok/Data/CBIS-DDSM_new", form = 'calc', mode = 'train', transform = None, train = True, preprocess = True, ROI = False):
        super(CBISDataset, self).__init__(form, mode, transform, train)
        self.train = train
        self.directory = os.path.join(directory, form + "_" + mode + "_new")
        self.df_dir = os.path.join(directory, f"{form}_case_description_{mode}_set.csv")
        self.transform = transform
        self.ROI = ROI
        self.dataframe = pd.read_csv(self.df_dir)
        self.df_len = len(self.dataframe)
        # print(self.df_len)
        print(self.val_ratio)
        
        # Control preprocessed here 
        self.preprocessed = preprocess
        self.file_name = self.preprocessFile(self.preprocessed)
        
        indices_list = self.generateTrainValSplit()
        self.data = []
        self.labels = []
        
        for i in range(self.df_len):
            if i in indices_list:
                row = self.dataframe.iloc[i]
                
                if not self.ROI: # Full images
                    full_img_folder = str(row['image file path']).split("/")[-2]
                    # label = row['class_label']
                    label = self.getLabel(str(row['pathology']))
                    image_path = os.path.join(self.directory, full_img_folder, self.file_name)
                    self.data.append(image_path)
                    self.labels.append(label)
                else: # ROI images
                    cropped_img_folder = str(row['cropped image file path']).split("/")[-2]
                    label = self.getLabel(str(row['pathology']))
                    image_path = os.path.join(self.directory, cropped_img_folder, self.file_name)
                    self.data.append(image_path)
                    self.labels.append(label)
    
        

class RSNADataset(CustomImageDataset):
    def __init__(self, directory = "/home/emok/sq58_scratch/emok/Data/RSNA", mode = 'train', transform = None, train = True, preprocessed = True):
        super(RSNADataset, self).__init__(mode, transform, train)
        self.mode = mode
        self.transform = transform
        self.train = train
        self.dataframe = pd.read_csv(self.df_dir)
        
        # Control preprocessed here 
        self.preprocessed = preprocessed
        self.file_name = self.preprocessFile(self.preprocessed)
        
        indices_list = self.generateTrainValSplit()
        
        self.data = []
        self.labels = []
        
        for i in range(len(self.dataframe)):
            if i in indices_list:
                row = self.dataframe.iloc[i]
                folder_name = row['patient_id']
                dcm_file = row['image_id']
                label = row['cancer']
                image_path = os.path.join(self.directory, self.mode, folder_name, dcm_file + ".dcm")
                self.data.append(image_path)
                self.labels.append(label)
    

class VinDrDataset(CustomImageDataset):
    def __init__(self, directory = "/home/emok/sq58/Code/Data/VinDr", mode="train", transform = None, train = True, preprocessed = True):
        super(VinDrDataset, self).__init__(mode, transform, train)
        self.mode = mode
        self.transform = transform
        self.train = train
        self.dataframe = pd.read_csv(self.df_dir)
        
        # Control preprocessed here
        self.preprocessed = preprocessed
        self.file_name = self.preprocessFile(self.preprocessed)
        
        indices_list = self.generateTrainValSplit()
        
        self.data = []
        self.labels = []
        
        for i in range(len(self.dataframe)):
            if i in indices_list:
                row = self.dataframe.iloc[i]
                folder_name = row['folder_name']
                dcm_file = row['image_id']
                label = row['cancer']
                image_path = os.path.join(self.directory, self.mode, folder_name, dcm_file + ".dicom")
                self.data.append(image_path)
                self.label.append(label)
    

class CMMDDataset(CustomImageDataset):
    def __init__(self, directory = "/home/emok/sq58/Code/Data/CMMD", mode = "train", transform=None, train = True, preprocessed = True):
        super(CMMDDataset, self).__init__(mode, transform, train)
        self.mode = mode
        self.transform = transform
        self.train = train
        self.dataframe = pd.read_csv(self.df_dir)
        
        # Control preprocessed here
        self.preprocessed = preprocessed
        self.file_name = self.preprocessFile(self.preprocessed)
        
        indices_list = self.generateTrainValSplit()
        self.data = []
        self.labels = []
        
        for i in range(len(self.dataframe)):
            if i in indices_list:
                row = self.dataframe.iloc[i]
                folder_name = row['folder_name']
                label = self.getLabel(str(row['classification']))
                image_path = os.path.join(self.directory, self.mode, str(i + 1), self.file_name)
                self.data.append(image_path)
                self.labels.append(label)
    
