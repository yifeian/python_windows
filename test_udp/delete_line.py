import fileinput

def test_delete():
    f = open(r'C:\Users\yifeifan\Desktop\new_change.txt','w')
    with open(r'C:\Users\yifeifan\Desktop\new2.txt','r') as file:
        for line in file.readlines():
            newline = line[18:]
            f.write(newline)
        f.close()
        file.close()

if __name__ == '__main__':
    test_delete()
