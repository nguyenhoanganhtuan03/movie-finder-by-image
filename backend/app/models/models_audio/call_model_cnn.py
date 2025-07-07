from tensorflow.keras.applications import ResNet50

def call_model(image_size=224):
    model = ResNet50(include_top=False, weights='imagenet', pooling='avg', input_shape=(image_size, image_size, 3))
    return model