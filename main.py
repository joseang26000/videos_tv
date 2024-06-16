import os
from googleapiclient.discovery import build
from pytube import YouTube
from datetime import datetime
import configparser
import glob
from os.path import expanduser

class Read_cfg():
    def __init__(self):
        pass

    def read_api(self):
        config = configparser.ConfigParser()
        config.read('configuration.cfg')
        api = config['Youtube']['api']
        return api


    def read_id_channels(self):
        config = configparser.ConfigParser()
        config.read('configuration.cfg')
        channels = config['Youtube']['channels']
        channels = channels.replace('\n', '')
        if channels[-1]==',':
            channels = channels[:-1]
        list_channels = channels.split(',')
        dic = {}
        for channel in list_channels:
            arr = channel.split(':')
            if len(arr)==2:
                dic[arr[0]] = arr[1].strip()
        return dic


    def read_path_videos(self):
        config = configparser.ConfigParser()
        config.read('configuration.cfg')
        path = config['Youtube']['path_videos']
        if path=="~/Youtube/":
            path = expanduser("~")+"/Youtube/"
        return path
    

class Delete_Videos():
    path = ""
    def __init__(self):
        conf = Read_cfg()
        self.path = conf.read_path_videos()
        

    def check_new_delete(self):
        l_videos = self.read_current_videos()
        l_videotimes = self.get_modification_time_videos(l_videos)
        day, month, year = self.get_date()
        current_total = self.get_total_time(day, month, year)
        l_deletevideos = self.get_videos_delete(l_videotimes, current_total)
        self.delete_videos(l_deletevideos)

    
    def delete_videos(self, videos):
        # Borrar el archivo
        for v in videos:
            try:
                os.remove(v)
                print(f"El archivo '{v}' ha sido borrado exitosamente.")
            except OSError as e:
                print(f"Error al borrar el archivo '{v}': {e}")
            

    def get_date(self):
        current_date = datetime.now().date()
        year = current_date.year
        month = current_date.month
        day = current_date.day
        return day, month, year
    

    def get_videos_delete(self, l_videotimes, current_total):
        l_delete = []
        for video in l_videotimes:
            total, v = video
            if (current_total-total) > 28:
                l_delete.append(v)
        return l_delete


    def read_current_videos(self):
        l_videos = []
        folders = os.listdir(self.path)
        for f in folders:
            p = self.path+f+'/*.mp4'
            videos = glob.glob(p)
            l_videos = l_videos+videos
        return l_videos
    
    
    def get_total_time(self, day, month, year):
        vday, vmonth, vyear = self.get_date()
        total = 0
        if year>2024:
            total = total + (year-vyear)*365
        total = total + month*30 + day
        return total


    def get_modification_time_videos(self, videos):
        l_wtimes = []
        for v in videos:
            info_video = os.path.getctime(v)
            creation_date = datetime.fromtimestamp(info_video)
            #l_wtimes.append([creation_date.day, creation_date.month, creation_date.year, v])
            total = self.get_total_time(creation_date.day, creation_date.month, creation_date.year)
            l_wtimes.append([total, v])
        return l_wtimes


class Download_Videos():
    api = ""
    dic_id = {}
    videos_path = ""
    def __init__(self):
        conf = Read_cfg()
        self.api = conf.read_api()
        self.dic_id = conf.read_id_channels()
        self.videos_path = conf.read_path_videos()


    def get_date(self):
        current_date = datetime.now().date()
        year = current_date.year
        month = current_date.month
        day = current_date.day
        return f'{day}-{month}-{year}'
    

    def check_new_videos(self):
        for channel in self.dic_id.keys():
            new_videos_items = self.get_info_last_videos(self.dic_id[channel], 5)
            new_videos_id = []
            for item in new_videos_items:
                new_videos_id.append(item['id']['videoId'])
            if os.path.exists(f'{self.videos_path}{channel}'):
                # Comprobar si está descargardo
                record_videos_id = self.read_record(channel)
                for id in new_videos_id:
                    if not (id in record_videos_id):
                        # Si el video no está descargado, descargar                    
                        self.download_video(id, channel)
                        self.update_record(channel, id, self.get_date())
            else:
                for item in new_videos_id:
                    self.download_video(item, channel)
                    self.update_record(channel, item, self.get_date())


    def get_info_last_videos(self, id_channel, number_videos):
        youtube = build('youtube', 'v3', developerKey=self.api)
        # Obtener la lista de videos del canal
        response = youtube.search().list(
            part='snippet',
            channelId=id_channel,
            order='date',
            type='video',
            maxResults=number_videos,
        ).execute()
        # Obtener el título del último video
        #latest_video_title = response['items'][0]['snippet']['title']
        last_videos = response['items']
        return last_videos


    def read_record(self, channel):
        ids_video = []
        # Abrir el archivo en modo de lectura ('r')
        with open(f'{self.videos_path}{channel}/.{channel}.csv', 'r') as archivo:
            # Iterar sobre cada línea del archivo
            for linea in archivo:
                # Hacer algo con cada línea (en este caso, imprimir)
                record = linea.split(';')
                ids_video.append(record[0].strip())
        return ids_video


    def update_record(self, channel, id_video, date_download):
        with open(f'{self.videos_path}{channel}/.{channel}.csv', 'a') as f:
            #f.write(f'{id_video};{date_download}\n')
            f.write(f'{id_video}\n')


    def download_video(self, id_video, channel):
        link = f'https://www.youtube.com/watch?v={id_video}'
        youtubeObject = YouTube(link)
        youtubeObject = youtubeObject.streams.get_highest_resolution()
        try:
            youtubeObject.download(f'{self.videos_path}{channel}')
        except:
            print("An error has occurred")
        print("Download is completed successfully")


if __name__ == '__main__':
    download =  Download_Videos()
    delete = Delete_Videos()
    download.check_new_videos()
    delete.check_new_delete()