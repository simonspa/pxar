#python script

f = open('007.raw','r')
file = f.read()
file = file.split()
nHeaders = 0
lengthData = 0
stacks = 0
for i in file:
    if i[0] == 'a':
        nHeaders +=1
        print '{0:3d}'.format(16*int(i[2], 16)+int(i[3], 16)),
        lengthData = 0
    if  i[0] == '0':
        lengthData += 1
    if  i[0] == 'c':
        print '{0:2d}'.format(int(i[3], 16)), '{0:2d}'.format(lengthData - 1)
        if int(i[3], 16) > 1: stacks += 1

print
print nHeaders, stacks

