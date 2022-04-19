import os
import pandas as pd
# import progressbar as pg

file_name = 'kernel_data.csv'
key_word = 'basics'
cmd = 'kaggle kernels list -s ' + key_word + ' --page-size 50 --sort-by scoreDescending --kernel-type all -v'

stream = os.popen(cmd)
output = stream.read()
with open(file_name, 'w') as file:
    file.write(output)
print('FILE:', file_name, 'CREATED')
stream.close()

kernel_data = pd.read_csv(file_name, sep=',', skipfooter=1, engine='python')
dimension = kernel_data.shape

# bar = pg.ProgressBar(max_value=dimension[0] - 1, redirect_stdout=True)
for i in range(dimension[0]):
    kernel = kernel_data.iloc[i, 0]
    cmd = 'kaggle kernels pull -p ../notebooks/ ' + kernel
    stream = os.popen(cmd)
    output = stream.read()
#   bar.update(i)
print('EOS')
