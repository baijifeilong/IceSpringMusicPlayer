# Created by BaiJiFeiLong@gmail.com at 2022/2/24 0:41

import array
import ctypes
import math


class FftHelper(object):
    def __init__(self):
        self.fftw3f = ctypes.CDLL(r"libfftw3f-3.dll")
        self.fftwf_plan_dft_r2c_1d = self.fftw3f.fftwf_plan_dft_r2c_1d
        self.fftwf_plan_dft_r2c_1d.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint)
        self.fftwf_plan_dft_r2c_1d.restype = ctypes.c_void_p
        self.fftwf_execute = self.fftw3f.fftwf_execute
        self.fftwf_execute.argtypes = (ctypes.c_void_p,)
        self.fftwf_execute.restype = None

    def rfft(self, inputs):
        size = len(inputs)
        outputs = array.array('f', [0.0] * (size * 2))
        input_ptr, _ = inputs.buffer_info()
        output_ptr, _ = outputs.buffer_info()
        fftwf_plan = self.fftwf_plan_dft_r2c_1d(size, input_ptr, output_ptr, 1)
        self.fftwf_execute(fftwf_plan)
        return outputs

    def rfftAbs(self, inputs):
        outputs = self.rfft(inputs)
        amplitudes = array.array('f', [0.0] * (len(inputs) // 2 + 1))
        for i in range(len(amplitudes)):
            amplitudes[i] = math.hypot(outputs[i * 2], outputs[i * 2 + 1])
        return amplitudes

    def rfftDbfs(self, inputs, sampleWidth):
        window = self.hanning(len(inputs))
        for i in range(len(inputs)):
            inputs[i] *= window[i]
        amplitudes = self.rfftAbs(inputs)
        windowSum = sum(window)
        for i in range(len(amplitudes)):
            magnitude = amplitudes[i] * 2 / windowSum / (2 ** (sampleWidth * 8 - 1))
            dbfs = -160 if magnitude < 2 ** -308 else 20 * math.log10(magnitude)
            amplitudes[i] = dbfs
        return amplitudes

    @staticmethod
    def rfftFreq(size, sampleRate):
        return [x / (size / sampleRate) for x in range(size // 2 + 1)]

    @staticmethod
    def hanning(size):
        return [0.5 * (1 - math.cos(2 * math.pi * i / (size - 1))) for i in range(size)]
