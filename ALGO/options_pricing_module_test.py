import ctypes


# for verifying the call and put option
if __name__ == '__main__':
    handle = ctypes.cdll. \
        LoadLibrary(r"C:\Users\fabio\source\repos\CallPricingDll\CallPricingDll\x64\Release\CallPricingDll.dll")

    handle.CallPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    handle.CallPricing.restype = ctypes.c_double
    handle.PutPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    handle.PutPricing.restype = ctypes.c_double

    inputs = """CALLS
    MRNA 354.54  115.0 6e-06 3.09 4.605473
    AMD  157.41  80.0  6e-06 3.09 3.378908
    TSLA 1135.89 50.0  6e-06 3.09 1.00e-05
    """
    inputs_1 = [354.54, 115.0, 6e-06, 3.09, 4.605473]
    inputs_2 = [157.41,  80.0,  6e-06, 3.09, 3.378908]
    inputs_3 = [1135.89, 50.0,  6e-06, 3.09, 1.00e-05]

    inputs_inputs = """PUTS
    MRNA 356.57 115.0 6e-06 3.09 3.12500
    AMD 157.51 80.0  6e-06 3.09 2.06250
    TSLA 1136.3 50.0  6e-06 3.09 8.00001
    """
    inputs_4 = [356.57, 115.0, 6e-06, 3.09, 3.12500]
    inputs_5 = [157.51, 80.0,  6e-06, 3.09, 2.06250]
    inputs_6 = [1136.3, 50.0,  6e-06, 3.09, 8.00001]

    call_inputs = [inputs_1, inputs_2, inputs_3]
    put_inputs = [inputs_4, inputs_5, inputs_6]

    spot = inputs_1[0]
    strike = inputs_1[1]
    ois_rate = inputs_1[2]
    days_till_expiration = inputs_1[3]
    sigma = inputs_1[4]
    call_price = handle.CallPricing(spot, strike, ois_rate, days_till_expiration, sigma)
    put_price = handle.PutPricing(spot, strike, ois_rate, days_till_expiration, sigma)
    print(call_price)
    print(put_price)
    """
    239.64157923543794
    0.10156484956207197
    """
    """
    239.572648706508
    0.0959671982419844
    """
