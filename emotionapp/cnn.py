import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
#for dirname, _, filenames in os.walk('/kaggle/input'):
    #for filename in filenames:
        #print(os.path.join(dirname, filename))
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import keras
from keras.preprocessing import image
from keras.models import Sequential
from keras.layers import Conv2D, MaxPool2D, Flatten,Dense,Dropout,BatchNormalization
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.densenet import DenseNet121, preprocess_input, decode_predictions
import cv2
from tensorflow.keras.applications import VGG16, InceptionResNetV2
from keras import regularizers
from tensorflow.keras.optimizers import Adam,RMSprop,SGD,Adamax

import random
seed = random.randint(1, 1000)
print(seed)


img_size = 100 #original size of the image
targetx = 100
targety = 100

epochs = 100
batch_size = 64

train_dir = "data/DATASET/train" #passing the path with training images
test_dir = "data/DATASET/test"   #passing the path with testing images

"""
Data Augmentation
--------------------------
"""

train_datagen = ImageDataGenerator(
        rescale=1./255, #  chuẩn hóa pixel về [0, 1].
        brightness_range=[0.9,1.1], # tăng cường dữ liệu bằng thay đổi độ sáng.
        horizontal_flip=True, # lật ảnh ngang ngẫu nhiên để tránh overfitting.
        fill_mode='nearest' 
)

test_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.5 # tách một nửa ảnh trong test_dir làm validation và một nửa làm test.
)

"""
Applying data augmentation to the images 
"""
train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(targetx, targety),
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=True,
        seed=seed,
       
)
val_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(targetx, targety),
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=False,
        seed=seed,
     subset="training"
        
)

test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(targetx, targety),
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=False,
    subset="validation",
        seed=seed
)

model= tf.keras.models.Sequential()
model.add(tf.keras.Input(shape=(targetx, targety, 3)))
model.add(Conv2D(32, kernel_size=(3, 3), padding='same', activation='relu'))
model.add(Conv2D(64,(3,3), padding='same', activation='relu' ))
model.add(BatchNormalization())
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(128,(5,5), padding='same', activation='relu'))
model.add(BatchNormalization())
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
    
model.add(Conv2D(512,(3,3), padding='same', activation='relu', kernel_regularizer=regularizers.l2(0.01)))
model.add(BatchNormalization())
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(0.25))



model.add(Conv2D(512,(3,3), padding='same', activation='relu', kernel_regularizer=regularizers.l2(0.01)))
model.add(BatchNormalization())
model.add(MaxPool2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten()) 
model.add(Dense(256,activation = 'relu'))
model.add(BatchNormalization())
model.add(Dropout(0.25))
    
model.add(Dense(512,activation = 'relu'))
model.add(BatchNormalization())
model.add(Dropout(0.25))

model.add(Dense(7, activation='softmax'))

model.compile(
    optimizer = Adam(learning_rate=0.0001), 
    loss='categorical_crossentropy', 
    metrics=['accuracy']
  )
model.summary()

# Fit the model
history = model.fit(x = train_generator,epochs = epochs,validation_data = val_generator)


# Evaluate the model
fig , ax = plt.subplots(1,2)
train_acc = history.history['accuracy']
train_loss = history.history['loss']
fig.set_size_inches(12,4)

ax[0].plot(history.history['accuracy'])
ax[0].plot(history.history['val_accuracy'])
ax[0].set_title('Training Accuracy vs Validation Accuracy')
ax[0].set_ylabel('Accuracy')
ax[0].set_xlabel('Epoch')
ax[0].legend(['Train', 'Validation'], loc='upper left')

ax[1].plot(history.history['loss'])
ax[1].plot(history.history['val_loss'])
ax[1].set_title('Training Loss vs Validation Loss')
ax[1].set_ylabel('Loss')
ax[1].set_xlabel('Epoch')
ax[1].legend(['Train', 'Validation'], loc='upper left')

plt.show()


model.save('model_optimal.h5')



import keras.utils as image
img = image.load_img("data/DATASET/test/1/test_0002_aligned.jpg",target_size = (targetx,targety,3))
img = np.array(img)
plt.imshow(img)
print(img.shape) #prints (48,48) that is the shape of our image


label_dict = {0:'SURPRISED',1:'FEARFUL',2:'DISGUSTED',3:'HAPPY',4:'SAD',5:'ANGRY',6:'NEUTRAL'}


img = np.expand_dims(img,axis = 0) #makes image shape (1,48,48)
img = img.reshape(1,targetx,targety,3)
result = model.predict(img)
result = list(result[0])
print(result)


img_index = result.index(max(result))
print(label_dict[img_index])
plt.show()


train_loss, train_acc = model.evaluate(train_generator)
val_loss, val_acc   = model.evaluate(val_generator)
print("final train accuracy = {:.2f} , validation accuracy = {:.2f}".format(train_acc*100, val_acc*100))


test_loss, test_acc   = model.evaluate(test_generator)
print("final test accuracy = {:.2f}".format(test_acc*100))


model.save_weights('model_weights.h5')