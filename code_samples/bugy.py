import csv

csv_file = open('../resources/colors.csv', newline='')
color_palette = csv.reader(csv_file, delimiter=' ')
colors = [c[0] for c in color_palette]
print(colors)
csv_file.close()
quit(0)
