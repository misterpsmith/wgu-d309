import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """Processes a song file.
    
    Artist information is inserted into the 'artists' table, and Song information
    is inserted into the 'songs' table.
    
    Args:
        cur (psycopg2.cursor): A database cursor
        filepath (string): A filepath to a song file
    """
    # open song file
    df = pd.read_json(filepath, lines=True)

    for index, row in df.iterrows():
        # insert song record
        song_data =  (row.song_id, row.title, row.artist_id, row.year, row.duration)
        try:
            cur.execute(song_table_insert, song_data)
        except psycopg2.Error as e:
            print("ERROR: Unable to insert record into 'songs' table.")
            print(e)
    
        # insert artist record
        artist_data = (row.artist_id, row.artist_name, row.artist_location, 
                       row.artist_latitude, row.artist_longitude)
        try:
            cur.execute(artist_table_insert, artist_data)
        except psycopg2.Error as e:
            print("ERROR: Unable to insert record into 'artists' table.")
            print(e)


def process_log_file(cur, filepath):
    """Processes a log file.
    
    Time information is inserted into the 'time' table. User information
    is upserted into the 'users' table. Songplay information is
    inserted into the 'songplays' table.
    
    Args:
        cur (psycopg2.cursor): A database cursor
        filepath (string): A filepath to a log file
    """
    # open log file
    df = pd.read_json(filepath, lines=True)

    # Check for empty userids - these are treated as empty strings and so must be removed or
    # the user table and songplays inserts will fail.  Remove the rows once found.
    df = df[(df['userId'].isin(['']))]

    # filter by NextSong action
    df =  df[df.page == 'NextSong']
    
    # convert timestamp column to datetime
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    t = df.copy()
    
    # insert time data records
    time_data =  (t.ts, t.ts.dt.hour , t.ts.dt.day , t.ts.dt.dayofweek , t.ts.dt.month ,
                  t.ts.dt.year , t.ts.dt.weekday)
    column_labels = ['start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday']
    time_df = pd.DataFrame(columns=column_labels)

    for index, column_label in enumerate(column_labels):
        time_df[column_label] = time_data[index]
    
    for i, row in time_df.iterrows():
        try:
            cur.execute(time_table_insert, list(row))
        except psycopg2.Error as e:
            print("ERROR: Unable to insert record into 'time' table.")
            print(e)

    # load user table
    user_df = df[['userId', 'firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        try:
            cur.execute(user_table_insert, row)
        except psycopg2.Error as e:
            print("ERROR: Unable to insert record into 'users' table.")
            print(e)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        try:
            cur.execute(song_select, (row.song, row.artist, row.length))
            results = cur.fetchone()
        
            if results:
                songid, artistid = results
            else:
                songid, artistid = None, None

            # insert songplay record
            songplay_data =  (row.ts, row.userId, row.level, songid, artistid,
                              row.sessionId, row.location, row.userAgent)
            try:
                cur.execute(songplay_table_insert, songplay_data)
            except psycopg2.Error as e:
                print("ERROR: Unable to insert record into 'songplays' table.")
                print(e)
        except psycopg2.Error as e:
            print("ERROR: Unable to query for song ID and artist ID.")
            print(e)


def process_data(cur, conn, filepath, func):
    """Processes JSON files for a data directory path.
    
    Valid function values can be 'process_song_file' or
    'process_log_file'.
    
    Args:
        cur (psycopg2.cursor): A database cursor
        conn (psycopg2.connection): A database connection
        filepath (string): A filepath of the directory to process
        func (function): The function to call for each found file
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    """Script main method.
    
    Creates a database connection, processes Song and Log information, and then
    closes the cursor and database connection.
    """
    try:
        conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    except psycopg2.Error as e:
        print("ERROR: Unable to make a connection to the PostgreSQL database.")
        print(e)
    try:
        cur = conn.cursor()
    except psycopg2.Error as e:
        print("ERROR: Unable to get a cursor to the PostgreSQL database.")
        print(e)

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()