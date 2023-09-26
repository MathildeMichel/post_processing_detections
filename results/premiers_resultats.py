import datetime as dt
import pandas as pd
import numpy as np
import easygui
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from collections import Counter
import seaborn as sns
from scipy import stats
import sys
import pytz


from utilities.def_func import get_csv_file, sorting_detections, t_rounder, get_timestamps, input_date, suntime_hour

# %% User inputs

files_list = get_csv_file(1)
df_detections, t_detections = sorting_detections(files_list, timebin_new=10, tz=pytz.FixedOffset(120), user_sel='intersection')

time_bin = list(set(t_detections['max_time']))
fmax = list(set(t_detections['max_freq']))
annotators = list(set(t_detections['annotators'].explode()))
labels = list(set(t_detections['labels'].explode()))
tz_data = df_detections['start_datetime'][0].tz

# Chose your mode :
# fixed : hard coded date interval
# auto : the script automatically extract the timestamp from the timestamp file
# input : you will fill a dialog box with the start and end date

dt_mode = 'fixed'

if dt_mode == 'fixed':
    begin_date = pd.Timestamp('2023-02-11 12:00:00 +0100')
    end_date = pd.Timestamp('2023-02-12 09:00:00 +0100')
elif dt_mode == 'auto':
    timestamps_file = get_timestamps()
    begin_date = pd.to_datetime(timestamps_file['timestamp'].iloc[0], format='%Y-%m-%dT%H:%M:%S.%f%z')
    end_date = pd.to_datetime(timestamps_file['timestamp'].iloc[-1], format='%Y-%m-%dT%H:%M:%S.%f%z') + dt.timedelta(seconds=time_bin[0])
elif dt_mode == 'input':
    begin_date = input_date('Enter begin date')
    end_date = input_date('Enter end date')

print("\ntime_bin: ", str(time_bin), "s", end='')
print("\nfmax: ", str(fmax), "Hz", end='')
print('\nannotators: ', str(annotators), end='')
print('\nlabels: ', str(labels), end='')
print('\nBegin date: {0}'.format(begin_date))
print('\nEnd date: {0}'.format(end_date))

# %% Overview plots

summary_label = df_detections.groupby('annotation')['annotator'].apply(Counter).unstack(fill_value=0)
summary_annotator = df_detections.groupby('annotator')['annotation'].apply(Counter).unstack(fill_value=0)

print('\n\t%%% Overview of the detections : %%%\n\n {0}'.format(summary_label))
print('\n\t-----------------------------------\n\n {0}'.format(summary_annotator.to_string()))

fig, (ax1, ax2) = plt.subplots(2, figsize=(10, 10), gridspec_kw={'height_ratios': [1, 1]}, facecolor='#36454F')
# ax1 = summary_label.plot(kind='bar', ax=ax1, color=['tab:blue', 'tab:orange'], edgecolor='black', linewidth=1)
ax1 = summary_label.plot(kind='bar', ax=ax1, edgecolor='black', linewidth=1)
ax2 = summary_annotator.plot(kind='bar', ax=ax2, edgecolor='black', linewidth=1)

# facecolor
ax1.set_facecolor('#36454F')
ax2.set_facecolor('#36454F')

# spacing between plots
plt.subplots_adjust(hspace=0.4)

# legend
ax1.legend(loc='best', fontsize=10, frameon=1, framealpha=0.6)
ax2.legend(loc='best', fontsize=10, frameon=1, framealpha=0.6)

# ticks
ax1.tick_params(axis='both', colors='w', rotation=0, labelsize=12)
ax2.tick_params(axis='both', colors='w', rotation=0, labelsize=12)

# labels
ax1.set_ylabel('Number of annotated calls', fontsize=15, color='w')
ax1.set_xlabel('Labels', fontsize=15, rotation=0, color='w')
ax2.set_ylabel('Number of annotated calls', fontsize=15, color='w')
ax2.set_xlabel('Annotator', fontsize=15, rotation=0, color='w')

# spines
ax1.spines['right'].set_visible(False)
ax1.spines['top'].set_visible(False)
ax1.spines['bottom'].set_color('w')
ax1.spines['left'].set_color('w')

ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.spines['bottom'].set_color('w')
ax2.spines['left'].set_color('w')

# y-grids
ax1.yaxis.grid(color='gray', linestyle='--')
ax2.yaxis.grid(color='gray', linestyle='--')
ax1.set_axisbelow(True)
ax2.set_axisbelow(True)

# titles
title_font = {'fontsize': 15, 'color': 'w', 'fontweight': 'bold'}
ax1.set_title('Number of annotations per label', color='w', fontdict=title_font, pad=5)
ax2.set_title('Number of annotations per annotator', color='w', fontdict=title_font, pad=5)


# %% Single seasonality plot

# ----------- User set mdate time xticks-----------------------------
# One tick per month
# mdate1 = mdates.MonthLocator(interval=1)
# mdate2 = mdates.DateFormatter('%B', tz=tz_data)
# One tick every 2 weeks
# mdate1 = mdates.DayLocator(interval=15, tz=tz_data)
# mdate2 = mdates.DateFormatter('%d-%B', tz=tz_data)
# One tick every day
# mdate1 = mdates.DayLocator(interval=1, tz=tz_data)
# mdate2 = mdates.DateFormatter('%d-%m', tz=tz_data)
# One tick every hour
mdate1 = mdates.HourLocator(interval=1, tz=tz_data)
mdate2 = mdates.DateFormatter('%H:%M', tz=tz_data)
# -------------------------------------------------------------------

annot_ref = easygui.buttonbox('Select an annotator', 'Single plot', annotators) if len(annotators) > 1 else annotators[0]
list_labels = t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['labels'].iloc[0]
label_ref = easygui.buttonbox('Select a label', 'Single plot', list_labels) if len(list_labels) > 1 else list_labels[0]
time_bin_ref = int(t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['max_time'].iloc[0])
file_ref = t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['file']

# Ask user if their resolution_bin is in minutes or in months or in seasons
resolution_bin = easygui.buttonbox(msg='Do you want to chose your resolution bin in minutes or in months', choices=('Minutes', 'Days', 'Weeks', 'Months'))
if resolution_bin == 'Minutes':
    res_min = easygui.integerbox('Enter the bin size (min)', 'Time resolution', default=10, lowerbound=1, upperbound=86400)
    n_annot_max = (res_min * 60) / time_bin_ref  # max nb of annoted time_bin max per res_min slice
    # Est-ce que c'est utile de garder start_vec et end_vec sachant qu'ils sont égaux à begin_date et end_date non ?
    delta, start_vec, end_vec = dt.timedelta(seconds=60 * res_min), t_rounder(begin_date, res=600), t_rounder(end_date + dt.timedelta(seconds=time_bin_ref), res=600)
    time_vector = [start_vec + i * delta for i in range(int((end_vec - start_vec) / delta) + 1)]
    y_label_txt = 'Number of detections\n({0} min)'.format(res_min)

elif resolution_bin == 'Days':
    time_vector_ts = pd.date_range(begin_date, end_date, freq='D', tz=tz_data)
    time_vector = [timestamp.date() for timestamp in time_vector_ts]
    n_annot_max = (24 * 60 * 60) / time_bin_ref
    y_label_txt = 'Number of detections per day'

elif resolution_bin == 'Weeks':
    time_vector_ts = pd.date_range(begin_date, end_date, freq='W-MON', tz=tz_data)
    time_vector = [timestamp.date() for timestamp in time_vector_ts]
    n_annot_max = (24 * 60 * 60 * 7) / time_bin_ref
    y_label_txt = 'Number of detections per week (starting every Monday)'
    

else:
    # Compute the time_vector for a monthly resolution
    time_vector_ts = pd.date_range(begin_date, end_date, freq='MS', tz=tz_data)
    time_vector = [timestamp.date() for timestamp in time_vector_ts]
    n_annot_max = (31 * 24 * 60 * 60) / time_bin_ref
    y_label_txt = 'Number of detections per month'


df_1annot_1label, _ = sorting_detections(file_ref, annotator=annot_ref, label=label_ref, timebin_new=time_bin_ref)

fig, ax = plt.subplots(figsize=(20, 9), facecolor='#36454F')
[hist_y, hist_x, _] = ax.hist(df_1annot_1label['start_datetime'], bins=time_vector, color='crimson', edgecolor='black', linewidth=1)

# Compute df_hist for user to check the values contained in the histogram
hist_xt = [pd.to_datetime(x * 24 * 60 * 60, unit='s') for x in hist_x[:-1]]
df_hist = pd.DataFrame({'Date': hist_xt, 'Number of detection': hist_y.tolist()})

# facecolor
ax.set_facecolor('#36454F')

# ticks
ax.tick_params(axis='y', colors='w', rotation=0, labelsize=20)
ax.tick_params(axis='x', colors='w', rotation=60, labelsize=15)


# Du coup c'est pas totalement exact par ce que j'ai calculé qu'un seul n_annot_max alors qu'en vrai il est différent chaque mois vu que tous les mois n'ont pas la même durée...

ax.set_ylabel(y_label_txt, fontsize=20, color='w')

# spines
ax.spines['right'].set_color('w')
ax.spines['top'].set_color('w')
ax.spines['bottom'].set_color('w')
ax.spines['left'].set_color('w')

# titles
fig.suptitle('annotateur : ' + annot_ref + '\n' + 'label : ' + label_ref, fontsize=24, y=0.98, color='w')

ax.xaxis.set_major_locator(mdate1)
ax.xaxis.set_major_formatter(mdate2)
plt.xlim(time_vector[0], time_vector[-1])
ax.grid(color='w', linestyle='--', linewidth=0.2, axis='both')

# Ask the user if they want to visualize the Figure in % or in raw values
choice_percentage = easygui.buttonbox(msg='Do you want your results plot in % or in raw values ?', choices=('Percentage', 'Raw values'))
if choice_percentage == 'Percentage':
    bars = range(0, 110, 2)  # from 0 to 100 step 10
    # y_pos = np.linspace(0, n_annot_max, num=len(bars))
    ax.set_yticks(y_pos, bars)
    ax.set_ylim([0,n_annot_max])
    y_pos = np.linspace(0, 100, num=len(bars))
    if resolution_bin == 'Minutes':
        ax.set_ylabel('Detection rate % \n({0} min)'.format(res_min), fontsize=20, color='w')
    else:
        ax.set_ylabel('Detection rate % per month', fontsize=20, color='w')

# %% Single diel pattern plot (scatter raw detections)

# ----------- User set mdate time xticks-----------------------------
# One tick per month
# mdate1 = mdates.MonthLocator(interval=1)
# mdate2 = mdates.DateFormatter('%B', tz=tz_data)
# One tick every 2 weeks
mdate1 = mdates.DayLocator(interval=15, tz=tz_data)
mdate2 = mdates.DateFormatter('%d-%B', tz=tz_data)
# One tick every day
# mdate1 = mdates.DayLocator(interval=1, tz=tz_data)
# mdate2 = mdates.DateFormatter('%d-%m', tz=tz_data)
# One tick every hour
# mdate1 = mdates.HourLocator(interval=1,tz=tz_data)
# mdate2 = mdates.DateFormatter('%H:%M', tz=tz_data)
# ----------------------------------------------------------------------------

# User input : gps coordinates in Decimal Degrees
title = "Coordinates en degree° minute' "
msg = "Latitudes (N/S) and longitudes (E/W)"
fieldNames = ["Lat Decimal Degree", "Lon Decimal Degree "]
fieldValues = []  # we start with blanks for the values
fieldValues = easygui.multenterbox(msg, title, fieldNames)

# make sure that none of the fields was left blank
while 1:
    if fieldValues is None: break
    errmsg = ""
    for i in range(len(fieldNames)):
        if fieldValues[i].strip() == "":
            errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
    if errmsg == "": break  # no problems found
    fieldValues = easygui.multpasswordbox(errmsg, title, fieldNames, fieldValues)
print("Reply was:", fieldValues)

lat = fieldValues[0]
lon = fieldValues[1]
# Compute sunrise and sunet decimal hour at the dataset location
[hour_sunrise, hour_sunset, _, _, _, _] = suntime_hour(begin_date, end_date, tz_data, lat, lon)

date_beg = begin_date.strftime('%Y-%m-%d')
date_end = end_date.strftime('%Y-%m-%d')

x_data = np.arange(date_beg, date_end, dtype="M8[D]")

t_detections_dt = [x.to_pydatetime() for x in df_detections['start_datetime']]

Day_det = t_detections_dt
Hour_det = [x.hour + x.minute / 60 for x in t_detections_dt]

# Plot figure
fig, ax = plt.subplots(figsize=(20, 10))
plt.plot(x_data, hour_sunrise, color='k')
plt.plot(x_data, hour_sunset, color='k')
plt.scatter(Day_det, Hour_det)

plt.xlim(begin_date, end_date)

ax.xaxis.set_major_locator(mdate1)
ax.xaxis.set_major_formatter(mdate2)
# plt.xlim(time_vector[0], time_vector[-1])
ax.grid(color='k', linestyle='-', linewidth=0.2)

plt.yticks(fontsize=20)
plt.xticks(fontsize=20)
ax.tick_params(axis='y', rotation=0, labelsize=20)
ax.tick_params(axis='x', rotation=60, labelsize=15)

ax.set_ylabel('Hour', fontsize=30)
ax.set_xlabel('Date', fontsize=30)

ax.set_title('Time of detections within each day for dataset {}'.format(df_detections['dataset'][0]), fontsize=40)


# %% Single diel pattern plot (Hourly detection rate)

# ----------- User set mdate time xticks-----------------------------
# One tick per month
mdate1 = mdates.MonthLocator(interval=1)
mdate2 = mdates.DateFormatter('%B', tz=tz_data)
# One tick every 2 weeks
# mdate1 = mdates.DayLocator(interval=15,tz=tz_data)
# mdate2 = mdates.DateFormatter('%d-%B', tz=tz_data)
# One tick every day
# mdate1 = mdates.DayLocator(interval=1, tz=tz_data)
# mdate2 = mdates.DateFormatter('%d-%m', tz=tz_data)
# One tick every hour
# mdate1 = mdates.HourLocator(interval=1,tz=tz_data)
# mdate2 = mdates.DateFormatter('%H:%M', tz=tz_data)
# ----------------------------------------------------------------------------

# User input : gps coordinates in Decimal Degrees
title = "Coordinates en degree° minute' "
msg = "Latitudes (N/S) and longitudes (E/W)"
fieldNames = ["Lat Decimal Degree", "Lon Decimal Degree "]
fieldValues = []  # we start with blanks for the values
fieldValues = easygui.multenterbox(msg, title, fieldNames)

# make sure that none of the fields was left blank
while 1:
    if fieldValues is None: break
    errmsg = ""
    for i in range(len(fieldNames)):
        if fieldValues[i].strip() == "":
            errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
    if errmsg == "": break  # no problems found
    fieldValues = easygui.multpasswordbox(errmsg, title, fieldNames, fieldValues)
print("Reply was:", fieldValues)

lat = fieldValues[0]
lon = fieldValues[1]
# Compute sunrise and sunet decimal hour at the dataset location
[hour_sunrise, hour_sunset, _, _, _, _] = suntime_hour(begin_date, end_date, tz_data, lat, lon)

date_beg = begin_date.strftime('%Y-%m-%d')
date_end = end_date.strftime('%Y-%m-%d')

x_data = np.arange(date_beg, date_end, dtype="M8[D]")

a = [dt.datetime.strftime(x, '%y-%m-%d') for x in df_detections['start_datetime']]
b = [dt.datetime.strftime(x, '%H') for x in df_detections['start_datetime']]
df_detections['date'] = a
df_detections['hour'] = b

det_groupby = df_detections.groupby(['date', 'hour']).size()
idx_day_groupby = det_groupby.index.get_level_values(0)
idx_hour_groupby = det_groupby.index.get_level_values(1)

time_vector_ts = pd.date_range(begin_date, end_date, freq='D', tz=tz_data)
time_vector_str = [dt.datetime.strftime(x, '%y-%m-%d') for x in time_vector_ts]


# arr = [[0]*cols]*rows
M = np.zeros((24, len(time_vector_str)))

for idx_j, j in enumerate(time_vector_str):

    # Search for detection in day = j
    f = [idx for idx, det in enumerate(idx_day_groupby) if det == j]
    if f:
        for ff in f:
            hour = idx_hour_groupby[ff]
            M[int(hour), idx_j] = det_groupby[ff]

x_lims = mdates.date2num((begin_date, end_date))
<<<<<<< Updated upstream
y_lims = [0,24]
cbarmax = 20
      
fig, ax = plt.subplots(figsize=(50, 15))
im = ax.imshow(M, extent = [x_lims[0], x_lims[1],  y_lims[0], y_lims[1]], vmin = 0, vmax = cbarmax, aspect='auto', origin='lower')
# Colorbar

cbar = fig.colorbar(im)
cbar.ax.tick_params(labelsize=30)
cbar.ax.set_ylabel('Nombre de minutes positives', rotation=270, fontsize = 30, labelpad = 40)

=======
y_lims = [0, 24]

fig, ax = plt.subplots(figsize=(40, 15))
ax.imshow(M, extent=[x_lims[0], x_lims[1], y_lims[0], y_lims[1]], aspect='auto', origin='lower')
>>>>>>> Stashed changes
plt.plot(x_data, hour_sunrise, color='w', linewidth=4)
plt.plot(x_data, hour_sunset, color='w', linewidth=4)
ax.xaxis_date()
ax.xaxis.set_major_locator(mdate1)
ax.xaxis.set_major_formatter(mdate2)

y_pos = [0, 4, 8, 12, 16, 20, 24]
ax.set_yticks(y_pos)

plt.yticks(fontsize=20)
plt.xticks(fontsize=20)
ax.tick_params(axis='y', rotation=0, labelsize=30)
ax.tick_params(axis='x', rotation=60, labelsize=30)

ax.set_ylabel('Heure (UTC +2)', fontsize=40)
ax.set_xlabel('Date', fontsize=40)

# ax.set_xticks(time_vector_str)


# %% Multilabel plot

if len(annotators) > 1:
    annot_ref = easygui.buttonbox('Select an annotator', 'multilabel plot', annotators) if len(annotators) > 1 else annotators[0]

elif len(annotators) == 1:
    annot_ref = annotators[0]

list_labels = t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['labels'].iloc[0]
time_bin_ref = int(t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['max_time'].iloc[0])
file_ref = t_detections[t_detections['annotators'].apply(lambda x: annot_ref in x)]['file']
if isinstance(list_labels, str) == 0:
    selected_labels = list_labels[0:3]  # TODO : checkbox to select desired labels to plot ?

    res_min = easygui.integerbox('Enter the bin size (min) ', 'Time resolution', default=10, lowerbound=1, upperbound=86400)
    delta, start_vec, end_vec = dt.timedelta(seconds=60 * res_min), t_rounder(begin_date, res=600), t_rounder(end_date + dt.timedelta(seconds=time_bin_ref), res=600)

    time_vector = [start_vec + i * delta for i in range(int((end_vec - start_vec) / delta) + 1)]

    time_slice = 60 * res_min  # 10 min
    n_annot_max = time_slice / time_bin_ref  # nb of annoted time_bin max per time_slice

    bars = range(0, 110, 10)  # from 0 to 100 step 10
    y_pos = np.linspace(0, n_annot_max, num=len(bars))

    fig, ax = plt.subplots(nrows=len(selected_labels), figsize=(25, 15), facecolor='#36454F')
    fig.tight_layout(pad=10)

    for i, label in enumerate(selected_labels):

        df_1annot_1label, _ = sorting_detections(file_ref, annotator=annot_ref, label=label)

        ax[i].hist(df_1annot_1label['start_datetime'], bins=time_vector, color='crimson', edgecolor='black', linewidth=1)

        bars = range(0, 110, 10)  # from 0 to 100 step 10
        y_pos = np.linspace(0, n_annot_max, num=len(bars))
        ax[i].set_facecolor('#36454F')
        ax[i].set_yticks(y_pos, bars)
        ax[i].tick_params(axis='both', colors='w', rotation=0, labelsize=15)
        ax[i].tick_params(axis='x', rotation=60)
        ax[i].set_title(label, fontsize=15, color='w')
        ax[i].set_ylabel('positive detection rate\n({0} min)'.format(res_min), fontsize=15, color='w')

        ax[i].xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=tz_data))
        ax[i].set_xlim(time_vector[0], time_vector[-1])
        ax[i].grid(color='w', linestyle='--', linewidth=0.2, axis='both')

    fig.suptitle('Annotator : {0}'.format(annot_ref), fontsize=25, y=0.98, color='w', weight='bold')

else: sys.exit('Multilabel plot cancelled, annotator {0} only has one label : {1}'.format(annot_ref, list_labels))

# %% Multi-user plot

if len(annotators) > 2:
    annot_ref1 = easygui.buttonbox('Select annotator 1', 'Plot label', annotators)
    annot_ref2 = easygui.buttonbox('Select an annotator', 'Plot label', [elem for elem in annotators if elem != annot_ref1])
elif len(annotators) < 2:
    sys.exit('Multi-user plot cancelled, not enough annotators to make a comparison')

else:
    annot_ref1 = annotators[0]
    annot_ref2 = annotators[1]

list_labels = t_detections[t_detections['annotators'].apply(lambda x: annot_ref1 in x)]['labels'].iloc[0]
if isinstance(list_labels, str) == 0:
    label_ref1 = easygui.buttonbox('Select a label for annotator 1 : {0}'.format(annot_ref1), 'Single plot', list_labels)
else:
    label_ref1 = list_labels
    easygui.msgbox('Only one label available for annotator 1, {0} : {1}'.format(annot_ref1, list_labels))
list_labels = t_detections[t_detections['annotators'].apply(lambda x: annot_ref2 in x)]['labels'].iloc[0]
if isinstance(list_labels, str) == 0:
    label_ref2 = easygui.buttonbox('Select a label for annotator 2 : {0}'.format(annot_ref2), 'Single plot', list_labels)
else:
    label_ref2 = list_labels
    easygui.msgbox('Only one label available for annotator 2, {0} : {1}'.format(annot_ref2, list_labels))

time_bin_ref1 = int(t_detections[t_detections['annotators'].apply(lambda x: annot_ref1 in x)]['max_time'].iloc[0])
time_bin_ref2 = int(t_detections[t_detections['annotators'].apply(lambda x: annot_ref2 in x)]['max_time'].iloc[0])
if time_bin_ref1 == time_bin_ref2:
    time_bin_ref = time_bin_ref1
else:
    sys.exit('The timebin of the detections {0}/{1} is {2}s whereas the timebin for {3}/{4} is {5}s!'.format(annot_ref1, label_ref1, time_bin_ref1, annot_ref2, label_ref2, time_bin_ref2))

file_ref1 = t_detections[t_detections['annotators'].apply(lambda x: annot_ref1 in x)]['file']
file_ref2 = t_detections[t_detections['annotators'].apply(lambda x: annot_ref2 in x)]['file']

res_min = easygui.integerbox('Enter the bin size (min) ', 'Time resolution', default=10, lowerbound=1, upperbound=86400)

delta, start_vec, end_vec = dt.timedelta(seconds=60 * res_min), t_rounder(begin_date, res=600), t_rounder(end_date + dt.timedelta(seconds=time_bin_ref), res=600)

time_vector = [start_vec + i * delta for i in range(int((end_vec - start_vec) / delta) + 1)]

n_annot_max = (res_min * 60) / time_bin_ref  # max nb of annoted time_bin max per res_min slice

df1_1annot_1label, _ = sorting_detections(files=file_ref1, annotator=annot_ref1, label=label_ref1, timebin_new=time_bin_ref)
df2_1annot_1label, _ = sorting_detections(files=file_ref2, annotator=annot_ref2, label=label_ref2, timebin_new=time_bin_ref)

fig, ax = plt.subplots(figsize=(16, 6), facecolor='#36454F')
ax.set_facecolor('#36454F')
hist_plot = ax.hist([df1_1annot_1label['start_datetime'], df2_1annot_1label['start_datetime']], bins=time_vector, label=[annot_ref1, annot_ref2], color=['coral', 'limegreen'], lw=10)
plt.legend(loc='upper right', fontsize=14)

bars = range(0, 110, 10)  # from 0 to 100 step 10
y_pos = np.linspace(0, n_annot_max, num=len(bars))
ax.set_yticks(y_pos, bars)
ax.tick_params(axis='x', rotation=60)
ax.tick_params(labelsize=20)
ax.set_ylabel('positive detection rate\n({0} min)'.format(res_min), fontsize=20, c='w')
ax.tick_params(axis='y')
fig.suptitle('[{0}/{1}] VS [{2}/{3}]'.format(annot_ref1, label_ref1, annot_ref2, label_ref2), color='w', fontsize=24, y=1.02)

ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=tz_data))
plt.xlim(time_vector[0], time_vector[-1])
# plt.xlim(time_vector[0], dt.datetime.strptime('2022-07-07T22-00-00', '%Y-%m-%dT%H-%M-%S'))
ax.grid(color='w', linestyle='-', linewidth=0.2, axis='both')
ax.tick_params(axis='both', colors='w')

# spines
ax.spines['right'].set_color('w')
ax.spines['top'].set_color('w')
ax.spines['bottom'].set_color('w')
ax.spines['left'].set_color('w')

# accord inter-annot
list1 = list(sorting_detections(file_ref1, annotator=annot_ref1, label=label_ref1, timebin_new=time_bin_ref)[0]['start_datetime'])
list2 = list(sorting_detections(file_ref2, annotator=annot_ref2, label=label_ref2, timebin_new=time_bin_ref)[0]['start_datetime'])

test1 = sorting_detections(file_ref1, annotator=annot_ref1, label=label_ref1, timebin_new=time_bin_ref)[0]
test2 = sorting_detections(file_ref2, annotator=annot_ref2, label=label_ref2, timebin_new=time_bin_ref)[0]

unique_annotations = len([elem for elem in list1 if elem not in list2]) + len([elem for elem in list2 if elem not in list1])
common_annotations = len([elem for elem in list1 if elem in list2])
print('Pourcentage d\'accord entre [{0}/{1}] & [{2}/{3}] : {4:.0f}%'.format(annot_ref1, label_ref1, annot_ref2, label_ref2, 100 * ((common_annotations) / (unique_annotations + common_annotations))))

# scatter
df_corr = pd.DataFrame(hist_plot[0] / n_annot_max, index=[annot_ref1, annot_ref2]).transpose()
plot = sns.lmplot(x=annot_ref1, y=annot_ref2, data=df_corr, scatter_kws={'s': 10, 'color': 'teal'}, fit_reg=True, markers='.', line_kws={'lw': 1, 'color': 'teal'})
plt.xlabel('{0}\n{1}'.format(annot_ref1, label_ref1))
plt.ylabel('{0}\n{1}'.format(annot_ref2, label_ref2))

plt.xlim(0, 1)
plt.ylim(0, 1)


def annotate(data, **kws):
    r, p = stats.pearsonr(data[annot_ref1], data[annot_ref2])
    ax = plt.gca()
    ax.text(.05, .8, 'R²={0:.2f}'.format(r * r),
            transform=ax.transAxes)


plot.map_dataframe(annotate)
plt.show()
