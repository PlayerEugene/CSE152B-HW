"""

"""

import numpy as np
# import tensorflow as tf
import cv2
from pathlib import Path

import torch
import torch.utils.data as data

# from .base_dataset import BaseDataset
# from .utils import pipeline
from utils.tools import dict_update

from models.homographies import sample_homography
from settings import DATA_PATH

from imageio import imread
def load_as_float(path):
    return imread(path).astype(np.float32)/255

class YoursDataset(data.Dataset):
    default_config = {
        'dataset': 'yours',  # or 'coco'
        'alteration': 'all',  # 'all', 'i' for illumination or 'v' for viewpoint
        'cache_in_memory': False,
        'truncate': None,
        'preprocessing': {
            'resize': False
        }
    }

    def __init__(self, transform=None, first_N=100,  **config):
        self.config = self.default_config
        self.config = dict_update(self.config, config)
        self.files = self._init_dataset(**self.config)
        sequence_set = []
        for (img, img_warped) in zip(self.files['image_paths'], self.files['warped_image_paths']):
            sample = {'image': img, 'warped_image': img_warped}
            sequence_set.append(sample)
        if first_N != -1:
            sequence_set = sequence_set[:first_N]
        self.samples = sequence_set
        self.transform = transform
        if config['preprocessing']['resize']:
            self.sizer = np.array(config['preprocessing']['resize'])
        pass

    def __getitem__(self, index):
        """

        :param index:
        :return:
            image:
                tensor (1,H,W)
            warped_image:
                tensor (1,H,W)
        """
        def _read_image(path):
            input_image = cv2.imread(path)
            return input_image

        def _preprocess(image):
            s = max(self.sizer /image.shape[:2])
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            image = image[:int(self.sizer[0]/s),:int(self.sizer[1]/s)]
            image = cv2.resize(image, (self.sizer[1], self.sizer[0]),
                                     interpolation=cv2.INTER_AREA)
            image = image.astype('float32') / 255.0
            if image.ndim == 2:
                image = image[:,:, np.newaxis]
            if self.transform is not None:
                image = self.transform(image)
            return image

        def _adapt_homography_to_preprocessing(image, H):
            # image = zip_data['image']
            # H = tf.cast(zip_data['homography'], tf.float32)
            # target_size = np.array(self.config['preprocessing']['resize'])
            s = max(self.sizer /image.shape[:2])
            # mat = np.array([[1,1,1/s], [1,1,1/s], [s,s,1]])
            mat = np.array([[1,1,s], [1,1,s], [1/s,1/s,1]])
            # down_scale = np.diag(np.array([1/s, 1/s, 1]))
            # up_scale = tf.diag(tf.stack([s, s, tf.constant(1.)]))
            # H = tf.matmul(up_scale, tf.matmul(H, down_scale))
            H = H*mat
            return H
        sample = self.samples[index]
        image_original = _read_image(sample['image'])
        image = _preprocess(image_original)
        warped_image = _preprocess(_read_image(sample['warped_image']))
        to_numpy = False
        if to_numpy:
            image, warped_image = np.array(image), np.array(warped_image)
        # homography = _adapt_homography_to_preprocessing(image_original, sample['homography'])
        sample = {'image': image, 'warped_image': warped_image}
        return sample

    def __len__(self):
        return len(self.samples)

    def _init_dataset(self, **config):
        image_paths = [config['im_path1']]
        warped_image_paths = [config['im_path2']]
        files = {'image_paths': image_paths,
                 'warped_image_paths': warped_image_paths}
        return files


