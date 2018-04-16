from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Reshape, Convolution2D, BatchNormalization, SpatialDropout2D, LeakyReLU
from keras.layers.core import Activation
from keras.layers.merge import concatenate
from keras.models import Model


def double_conv_layer(x, size, dropout, batch_norm):
    conv = Conv2D(size, (3, 3), padding='same')(x)
    if batch_norm is True:
        conv = BatchNormalization()(conv)
    conv = Activation('relu')(conv)
    conv = Conv2D(size, (3, 3), padding='same')(conv)
    if batch_norm is True:
        conv = BatchNormalization()(conv)
    conv = Activation('relu')(conv)
    if dropout > 0:
        conv = SpatialDropout2D(dropout)(conv)
    return conv


def double_dilated_conv_layer(x, size, dilation_rate, dropout: float, batch_norm: bool, activation='relu'):
    conv = Convolution2D(size, (3, 3), dilation_rate=dilation_rate, padding='same')(x)
    if batch_norm is True:
        conv = BatchNormalization()(conv)

    if activation == 'leaky_relu':
        conv = LeakyReLU()(conv)
    else:
        conv = Activation(activation)(conv)

    conv = Convolution2D(size, (3, 3), dilation_rate=dilation_rate, padding='same')(conv)
    if batch_norm is True:
        conv = BatchNormalization()(conv)

    if activation == 'leaky_relu':
        conv = LeakyReLU()(conv)
    else:
        conv = Activation(activation)(conv)

    if dropout > 0:
        conv = SpatialDropout2D(dropout)(conv)

    return conv


def DilatedUnet(dropout_val=0.1,
                filters=32,
                batch_norm=True,
                patch_size=224,
                input_channels=3,
                output_classes=1):
    inputs = Input((patch_size, patch_size, input_channels))
    axis = 3

    conv_224 = double_conv_layer(inputs, filters, dropout_val, batch_norm)
    pool_112 = MaxPooling2D(pool_size=(2, 2), name='pool_112')(conv_224)

    conv_112 = double_conv_layer(pool_112, 2 * filters, dropout_val, batch_norm)
    pool_56 = MaxPooling2D(pool_size=(2, 2), name='pool_56')(conv_112)

    conv_56 = double_conv_layer(pool_56, 4 * filters, dropout_val, batch_norm)
    pool_28 = MaxPooling2D(pool_size=(2, 2))(conv_56)

    conv_28 = double_conv_layer(pool_28, 8 * filters, dropout_val, batch_norm)
    pool_14 = MaxPooling2D(pool_size=(2, 2))(conv_28)

    conv_14 = double_conv_layer(pool_14, 16 * filters, dropout_val, batch_norm)
    pool_7 = MaxPooling2D(pool_size=(2, 2))(conv_14)

    conv_7 = double_conv_layer(pool_7, 32 * filters, dropout_val, batch_norm)

    up_14 = concatenate([UpSampling2D(size=(2, 2))(conv_7), conv_14], axis=axis)
    up_conv_14 = double_dilated_conv_layer(up_14, 16 * filters, 2, dropout_val, batch_norm)

    up_28 = concatenate([UpSampling2D(size=(2, 2))(up_conv_14), conv_28], axis=axis)
    up_conv_28 = double_dilated_conv_layer(up_28, 8 * filters, 2, dropout_val, batch_norm)

    up_56 = concatenate([UpSampling2D(size=(2, 2))(up_conv_28), conv_56], axis=axis)
    up_conv_56 = double_dilated_conv_layer(up_56, 4 * filters, 2, dropout_val, batch_norm)

    up_112 = concatenate([UpSampling2D(size=(2, 2))(up_conv_56), conv_112], axis=axis)
    up_conv_112 = double_dilated_conv_layer(up_112, 2 * filters, 3, dropout_val, batch_norm)

    up_224 = concatenate([UpSampling2D(size=(2, 2))(up_conv_112), conv_224], axis=axis)
    up_conv_224 = double_dilated_conv_layer(up_224, filters, 4, dropout_val, batch_norm)

    conv_final = Conv2D(output_classes, (1, 1))(up_conv_224)

    if output_classes == 1:
        conv_final = Activation('sigmoid')(conv_final)
    else:
        conv_final = Activation('softmax')(conv_final)

    model = Model(inputs, conv_final, name="DilatedUnet")

    return model