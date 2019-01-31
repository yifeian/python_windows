def str_to_hex(s):
    return ' '.join([hex(ord(c)).replace('0x', '') for c in s])
data = str_to_hex("62673532672063616c6c206964205b315d")
print(data)
print(data.replace(' ',''))

def hex_to_str(s):
    return ''.join([chr(i) for i in [int(b, 16) for b in s.split(' ')]])

print(hex_to_str(data))
