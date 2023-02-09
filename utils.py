import math

PI = 3.1415926535897932384626
A = 6378245.0
EE = 0.00669342162296594323


class CPrint(object):
    TEXT_BOX = None

    def __init__(self):
        pass

    def set_text_box(text_box):
        CPrint.TEXT_BOX = text_box

    def print(text):
        print(text)
        if CPrint.TEXT_BOX:
            CPrint.TEXT_BOX.insert("end", text+"\n")


def str_to_gps84(in_data1, in_data2):
    len_data1 = len(in_data1)
    str_data2 = "%05d" % int(in_data2)
    temp_data = int(in_data1)
    symbol = 1
    if temp_data < 0:
        symbol = -1
    degree = int(temp_data / 100.0)
    str_decimal = str(in_data1[len_data1-2]) + \
        str(in_data1[len_data1-1]) + '.' + str(str_data2)
    f_degree = float(str_decimal)/60.0
    # print("f_degree:", f_degree)
    if symbol > 0:
        result = degree + f_degree
    else:
        result = degree - f_degree
    return result


def gps84_to_gcj02(lat, lng):
    if out_of_china(lat, lng):
        return [0, 0]
    dLat = transform_lat(lng - 105.0, lat - 35.0)
    dLon = transform_lng(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * PI
    magic = math.sin(radLat)
    magic = 1 - EE * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((A * (1 - EE)) /
                             (magic * sqrtMagic) * PI)
    dLon = (dLon * 180.0) / (A /
                             sqrtMagic * math.cos(radLat) * PI)
    mgLat = lat + dLat
    mgLon = lng + dLon
    return [mgLat, mgLon]


def gcj02_to_bd09(gg_lat, gg_lng):
    x = gg_lng
    y = gg_lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * PI)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lat, bd_lng]


def out_of_china(lat, lng):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def transform(lat, lng):
    if out_of_china(lat, lng):
        return [lat, lng]
    dLat = transform_lat(lng - 105.0, lat - 35.0)
    dLon = transform_lng(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * PI
    magic = math.sin(radLat)
    magic = 1 - EE * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((A * (1 - EE)) /
                             (magic * sqrtMagic) * PI)
    dLon = (dLon * 180.0) / (A /
                             sqrtMagic * math.cos(radLat) * PI)
    mgLat = lat + dLat
    mgLon = lng + dLon
    return [mgLat, mgLon]


def transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * \
        y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 *
            math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 *
            math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320 *
            math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + \
        0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 *
            math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 *
            math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 *
            math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret
