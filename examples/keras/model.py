"""
This example uses a pretrained model (https://github.com/nyukat/breast_cancer_classifier)

This is an implementation of the model used for breast cancer classification as described in our paper Deep Neural Networks Improve Radiologists' Performance in Breast Cancer Screening. The implementation allows users to get breast cancer predictions by applying one of our pretrained models: a model which takes images as input (image-only) and a model which takes images and heatmaps as input (image-and-heatmaps).

    Input images: 2 CC view mammography images of size 2677x1942 and 2 MLO view mammography images of size 2974x1748. Each image is saved as 16-bit png file and gets standardized separately before being fed to the models.
    Input heatmaps: output of the patch classifier constructed to be the same size as its corresponding mammogram. Two heatmaps are generated for each mammogram, one for benign and one for malignant category. The value of each pixel in both of them is between 0 and 1.
    Output: 2 predictions for each breast, probability of benign and malignant findings: left_benign, right_benign, left_malignant, and right_malignant.




"""




from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from lume_model.models import SurrogateModel
import numpy as np

model = ResNet50(weights='imagenet')

img_path = 'elephant.jpg'
img = image.load_img(img_path, target_size=(224, 224))
x = image.img_to_array(img)


x = np.expand_dims(x, axis=0)
x = preprocess_input(x)

preds = model.predict(x)
# decode the results into a list of tuples (class, description, probability)
# (one such list for each sample in the batch)
print('Predicted:', decode_predictions(preds, top=3)[0])
# Predicted: [(u'n02504013', u'Indian_elephant', 0.82658225), (u'n01871265', u'tusker', 0.1122357), (u'n02504458', u'African_elephant', 0.061040461)]


class ResnetModel(SurrogateModel):

    input_variables = {
        "image_input": InputImageVariable(
            name = "image_input",
            default = ,
            x_max =224,
            y_max =224,
            x_max = 0,
            y_max = 0
        )
    }

    output_variables = {
        "input_"

    }