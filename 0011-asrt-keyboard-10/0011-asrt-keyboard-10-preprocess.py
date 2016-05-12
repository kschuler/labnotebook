
# coding: utf-8

# # 0011 aSRT Keyboard 10
# 
# This is the data analysis of experiment 00101 aSRT keyboard 10. This analysis includes every step from the original raw-data files to the final results output for this experiment (including figures). Katie runs the majority of her data analysis in the ipython notebook, with some additional analysis run in SPSS.
# 
# ### Import required packages and setup
# 
# Before we begin our analysis, we import some required packages and specify our desired figure settings.

# In[1]:

#import packages (required for analysis)
get_ipython().magic(u'pylab inline')
import numpy as np
import pandas as pd
from scipy import stats, optimize
import matplotlib.pyplot as plt
import seaborn as sns
import os, csv
import statsmodels.api as sm


# In[2]:

#figure settings
sns.set(style="whitegrid", palette="deep")


# 
# Next, we set some useful parameters to tell pandas where our data and required files are located.

# In[3]:

#params (change these for every experiment)
exp_id = '0011'
exp_title = 'aSRT-keyboard-10'

#paths to files we need
path_raw = '/Users/kathrynschuler/Documents/current/research/raw-data/'+exp_id+'-'+exp_title+'-data'
path_track = '/Users/kathrynschuler/Documents/current/research/subject-tracking/'+exp_id+'-'+exp_title+'-track.csv'

#list the data files we have
file_list = os.listdir(path_raw)


# In[4]:

print file_list


# ## Data pre-processing
# 
# ### Rationale for pre-processing
# Because this was the first experiment that I ran, some helpful fields are missing from the automatic data output.  It is necessary to preprocess the data to come up with some of the fields required by the analysis used in [Howard and Howard, 1997](http://psycnet.apa.org/journals/pag/12/4/634/), which is the analysis that we want to replicate.
# 
# 
# ### Add header and load all data
# As a first step, we add a header row (which was not included in the original data output).  
# 
# Then, we can read all of the raw data files into pandas, creating one long ```all_data``` data frame.  We also merge this data frame with our ```subj_track``` data frame, so all of our data is accessable in one place.
# 

# In[5]:

#add a header to data files
header = ['gender', 'experimenter', 'name', 'circle_num', 'circle_name', 'circle_key', 'attempt_no', 'cum_time', 'key_pressed', 'RT', 'isCorrect']

#read into pandas (names=header)
raw_data = [pd.read_csv(path_raw+'/'+file, header=None, names=header, index_col=False) for file in file_list]

#concatenate all raw data files together
all_data = pd.concat(raw_data)

#read subject tracking into pandas 
subj_track = pd.read_csv(path_track)

#merge add_data and subj_track
new_data = pd.merge(subj_track, all_data, on='name')


# In[6]:


all_data.head(10)


# This leaves us with a bunch of columns that aren't really relevant for the data analysis we are interested in (but we preserve in our raw data in case we ever need them).  Let's remove these columns to simplify our data frame.

# In[7]:

#include only relevant columns, and leave out subjects marked for exclusion.
new_data = new_data[['date','sid', 'circle_key', 'key_pressed', 'RT', 'KDS-exclude', 'attempt_no', 'isCorrect']]
final_data = new_data[new_data['KDS-exclude'] == False]



# In[ ]:




# ### Add some required variables
# 
# Next we need to ID trials as either a pattern trial or a random trial.  To simplify things, we can first remove data from our ```all-data``` data frame where ```attempt-no``` is equal to 2.  This is because it means that our subject chose the wrong button on the first attempt, which winds up being excluded data, so we don't need to know their reaction times on their second attempt.
# 
# We do, however, want to know whether subjects were correct or not on the first trial.  This information is already saved as a boolean value in the ```isCorrect``` column.  Therefore, we are free to remove any trials where ```attempt-no``` is equal to 2.

# In[8]:

# get a data frame of first attempts only
first_attempts = final_data[final_data.attempt_no == 1] 


# After this, we need to add a trial number for every subject. We can also group our data by subject and get a count for each column to confirm that we are seeing the number of trials we expect.

# In[9]:

def add_trial_num(df):
    '''adds a trial number'''
    df['trial'] = np.arange(len(df['attempt_no'])) + 1
    return df

trial_data = first_attempts.groupby('sid').apply(add_trial_num)
trial_data.groupby('sid').count()


# In this case, we see that we have 1600 trials - as we expected.  We also notice that there are 20 subjects in this experiment.
# 
# To find out the dates this experiment was run, we create a date-time value, and then ask pandas to describe the data in this column.
# 
# 

# In[10]:

trial_data['date'] = pd.to_datetime(trial_data['date'])

print trial_data['date'].describe()


# We see that there were 10 unique dates, with the first date being October 24, 2012 and the last date being November 15, 2012.  This is the date range for this experiment.
# 
# 
# Next we need to add a new block for every 80 trials.

# In[11]:

def add_block_num(df):
    blocks = []
    for block in arange(1, 11):
        blocks.extend(repeat(block, 80))
    df['block'] = blocks
    return df

trial_data = trial_data.groupby('sid').apply(add_block_num)


# In[12]:

print trial_data.head()


# We also need to add a ```gblock``` variable, which allows us to group the blocks into a certain number of "sessions".  In this case, let's use 2.  This means we will have a new ```gblock``` every 400 trials (or every 5 blocks).

# In[13]:

def add_group_block_num(df):
    gblocks = []
    for gblock in arange(1, 6):
        gblocks.extend(repeat(gblock, 160))
    df['gblocks'] = gblocks
    return df

trial_data = trial_data.groupby('sid').apply(add_group_block_num)


# Then we need to add whether this was a pattern or random trial

# In[14]:

#add column for type (even trials are always random)
trial_data['type'] = trial_data['trial'].apply(lambda x: 'random' if x%2==0 else 'pattern')


# and add the precise pattern this particular subject had

# In[15]:

#add column for specific pattern
trial_data['pattern'] = trial_data.sid.map(trial_data.groupby('sid')['circle_key'].apply(lambda x: list(x[:7:2])))


# After this, we will list the possible values for the triplets (e.g. triplet 1x4, or 2x3, where x is any random number.  Because we don't care what the value of x is, we will only attend to the first and last element of the triplet.

# In[16]:

#list possible triplet combinations
def getCombos(pattern):
    pattern = pattern + [pattern[0]]
    return ''.join(pattern)

trial_data['combos'] = trial_data.pattern.map(getCombos)


# In[17]:

print trial_data.head()


# In[18]:

#get this trial and 2 trials ago
trial_data['shifted'] = pd.concat([trial_data.groupby('sid')['circle_key'].shift(2) + trial_data.groupby('sid')['circle_key'].shift(0)])


# Find out if this is a high-frequency of low-freqnecy triplet (part of pattern or no)
# 

# In[19]:

#is it a HF triplet?
def func(df):
    return str(df.shifted) in df.combos

trial_data['high-freq'] = trial_data.apply(func, axis=1)


# And create a column that lets us know whether this is HF-pattern, HF-random, or LF-random.

# In[20]:

#HF random or HF pattern?
def f_type(df):
    if df['high-freq'] == True and df.type == 'pattern':
        return 'HF-pattern'
    elif df['high-freq'] == True and df.type == 'random':
        return 'HF-random'
    else:
        return 'LF-random'

trial_data['f_type'] = trial_data.apply(f_type, axis=1)
print trial_data.head(10)


# ### Remove unwanted values
# 
# Recall that the aSRT paradigm we are modeling our experiment after removes particular trial types in order to eliminate potentially spurious reaction times (i.e. "trills" and "reps", because these things are "easier" for the subjects)
# 
# To do this, we can ask whether the current trial is the same as a previous trial.

# In[21]:

trial_data['previous_two'] = pd.concat([trial_data.groupby('sid')['circle_key'].shift(2) + trial_data.groupby('sid')['circle_key'].shift(1)])

def func(df):
    return str(df.circle_key) in str(df.previous_two)

trial_data['isRep'] = trial_data.apply(func, axis=1)

print trial_data.head()


# In[22]:

trial_data.to_csv("/Users/kathrynschuler/Documents/current/research/raw-data-processed/0011-aSRT-keyboard-10-processed.csv", sep = ",")


