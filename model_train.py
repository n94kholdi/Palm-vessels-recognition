import tensorflow as tf
import numpy as np
import pandas as pd
import matplotlib
import cv2
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pickle
from Preprocess import PreprocessLayer, PreprocessLayer_2

# PROCESSED_TRAIN_PATH = "./Data_600_vessels/"
PROCESSED_TRAIN_PATH = "./Data/"
PROCESSED_VALID_PATH = "../Data/Final/valid/"
PROCESSED_TEST_PATH = "../Data/Final/test/"
EPOCHS = 300
BATCH_SIZE = 32
INPUT_SIZE = (128, 128, 3)


if __name__ == "__main__":
    vgg_model = tf.keras.applications.vgg16.VGG16(weights='imagenet', include_top=False, input_shape=INPUT_SIZE)
    # vgg_model = tf.keras.applications.resnet.ResNet152(weights='imagenet', include_top=False, input_shape=INPUT_SIZE)
    vgg_model.trainable = False

    model = tf.keras.models.Sequential()

    # model.add(preprocess)
    model.add(vgg_model)
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(1024))
    model.add(tf.keras.layers.Activation('relu'))
    model.add(tf.keras.layers.Dropout(0.5))
    model.add(tf.keras.layers.Dense(600))
    model.add(tf.keras.layers.Activation('softmax'))

    print(model.summary())

    sgd = tf.keras.optimizers.SGD(lr=0.0005, decay=1e-7, momentum=0.9, nesterov=True)
    adam = tf.keras.optimizers.Adam(lr=0.00005, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.001, amsgrad=False)

    # model = tf.keras.models.load_model('./Saved_models/Classifier/myCNN.h5')
    #
    # print(model.summary())

    model.compile(loss=tf.keras.losses.categorical_crossentropy,
                  optimizer=sgd,
                  metrics=['accuracy'])

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1. / 255,
                                                                    width_shift_range=0.5,
                                                                    height_shift_range=0.5,
                                                                    zoom_range=0.3,
                                                                    brightness_range=[0.7, 1.7],
                                                                    rotation_range=30,
                                                                    validation_split=0.2)
                                                                    #preprocessing_function=PreprocessLayer)

    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1. / 255)
                                                                   #preprocessing_function=PreprocessLayer)

    val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255,
                                                                  validation_split=0.)
                                                                  #preprocessing_function=PreprocessLayer)


    train_loader = train_datagen.flow_from_directory(PROCESSED_TRAIN_PATH, batch_size=BATCH_SIZE,
                                                     target_size=INPUT_SIZE[:2], subset='training')
    valid_loader = train_datagen.flow_from_directory(PROCESSED_TRAIN_PATH, batch_size=BATCH_SIZE,
                                                     target_size=INPUT_SIZE[:2], subset='validation')

    Checkpoint = tf.keras.callbacks.ModelCheckpoint('./Saved_models/Classifier/myCNN.h5', monitor='val_accuracy',
                                                    mode='max', verbose=0,
                                                    save_best_only=True, save_weights_only=False, period=1)


    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', min_delta=0, patience=10, verbose=1,
                                                      mode='max')
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2,
                                                     patience=5, min_lr=0.0001)
    csv_logger = tf.keras.callbacks.CSVLogger('./Saved_models/Classifier/log.csv', append=True, separator=';')


    history = model.fit_generator(
        train_loader,
        steps_per_epoch=train_loader.samples // BATCH_SIZE,
        epochs=EPOCHS,
        verbose=1,
        validation_data=valid_loader,
        validation_steps=valid_loader.samples // BATCH_SIZE,
        callbacks=[Checkpoint, reduce_lr, csv_logger])
        # callbacks=[Checkpoint, early_stopping, reduce_lr, csv_logger])

    #######################
    #### Fine Tuning: #####

    vgg_model.trainable = True
    print(model.summary())

    model.compile(loss=tf.keras.losses.categorical_crossentropy,
                  optimizer=adam,
                  metrics=['accuracy'])

    history = model.fit_generator(
        train_loader,
        steps_per_epoch=train_loader.samples // BATCH_SIZE,
        epochs=50,
        verbose=1,
        validation_data=valid_loader,
        validation_steps=valid_loader.samples // BATCH_SIZE,
        callbacks=[Checkpoint, reduce_lr, csv_logger])

    # test_loader = test_datagen.flow_from_directory(PROCESSED_TEST_PATH, batch_size=BATCH_SIZE,
    #                                                target_size=INPUT_SIZE[:2])

    # best_model = tf.keras.models.load_model('./Saved_models/Classifier/myCNN.h5')

    # score = best_model.evaluate_generator(test_loader)

    # print("Test Accuracy: {:.4f}".format(score[1]))

    with open('trainHistoryDict', 'wb') as file_pi:
        pickle.dump(history.history, file_pi)

    file_in = open('trainHistoryDict', 'rb')
    history = pickle.load(file_in, encoding='latin1')

    pd.DataFrame(history).to_csv('history.csv')

    # summarize history for accuracy
    plt.plot(history['accuracy'])
    plt.plot(history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.savefig("./Saved_models/Classifier/accuracy.jpg")
    plt.clf()
    # summarize history for loss
    plt.plot(history['loss'])
    plt.plot(history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.savefig("./Saved_models/Classifier/loss.jpg")

