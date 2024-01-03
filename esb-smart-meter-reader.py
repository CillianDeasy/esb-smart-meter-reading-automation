
# #!/usr/bin/env python3

import sys
import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import configparser
import datetime, pytz
import logging
from influxdb import InfluxDBClient
from copy import deepcopy



formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


class EsbDataCollection:
  
  def __init__(self, username, password, mprn) -> None:
    self.username = username
    self.password = password
    self.mprn = mprn

    
    self.csv = None
    self.json = None
    

  def __load_esb_data(self, start_date):
    logger.info('Opening session...')
    s = requests.Session()
    s.headers.update({
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
    }) 
    
    logger.info('Getting login page')
    try:
      login_page = s.get('https://myaccount.esbnetworks.ie/', allow_redirects=True)
      result = re.findall(r"(?<=var SETTINGS = )\S*;", str(login_page.content))
      settings = json.loads(result[0][:-1])
    except Exception as e:
      logger.exception(e)
    
    logger.info('Sending credentials')
    try:
      s.post(
        'https://login.esbnetworks.ie/esbntwkscustportalprdb2c01.onmicrosoft.com/B2C_1A_signup_signin/SelfAsserted?tx=' + settings['transId'] + '&p=B2C_1A_signup_signin', 
        data={
          'signInName': self.username, 
          'password': self.password, 
          'request_type': 'RESPONSE'
        },
        headers={
          'x-csrf-token': settings['csrf'],
        },
        allow_redirects=False)
    except Exception as e:
      logger.exception(e)
    logger.info('Passing authentication')
    try:
      confirm_login = s.get(
        'https://login.esbnetworks.ie/esbntwkscustportalprdb2c01.onmicrosoft.com/B2C_1A_signup_signin/api/CombinedSigninAndSignup/confirmed',
        params={
          'rememberMe': False,
          'csrf_token': settings['csrf'],
          'tx': settings['transId'],
          'p': 'B2C_1A_signup_signin',
        }
      )
    except Exception as e:
      logger.exception(e)
    
    logger.debug('login confirmed: %s' % confirm_login)
    logger.info('parsing content')
    soup = BeautifulSoup(confirm_login.content, 'html.parser')
    form = soup.find('form', {'id': 'auto'})
    s.post(
      form['action'],
      allow_redirects=False,
      data={
        'state': form.find('input', {'name': 'state'})['value'],
        'client_info': form.find('input', {'name': 'client_info'})['value'],
        'code': form.find('input', {'name': 'code'})['value'],
      }, 
    )
    
    logger.info('Getting data using v2 URL')
    try:
      data = s.get('https://myaccount.esbnetworks.ie/DataHub/DownloadHdf?mprn=' + self.mprn + '&startDate=' + start_date.strftime('%Y-%m-%d'))
    except Exception as e:
      logger.error('Failed to retrieve data using v2 endpoint: %s' % e)
      
    data_decoded = data.content.decode('utf-8').splitlines()
    logger.info('%s records retrieved and decoded.' % len(data_decoded))
    return data_decoded


  def get_csv_data(self):
    today = datetime.datetime.today()
    
    if self.csv is None:
      self.csv = self.__load_esb_data(today)
    
    return self.csv
  
  def get_json_data(self):
    
    if self.json is None:
      self.json = []
    
      csv_reader = csv.DictReader( self.get_csv_data() )
      for row in csv_reader:
        self.json.append(row)
      
    return self.json
    

def convert_to_unix(local_time):
  utc = pytz.utc
  epoch = datetime.datetime(1970,1,1,0,0,0,tzinfo=pytz.UTC)
  local = pytz.timezone("Europe/Dublin")
  local_fmt = '%d-%m-%Y %H:%M'
  
  dt = datetime.datetime.strptime(local_time, local_fmt)
  adjusted = local.localize(dt)
  
  utc_ts = adjusted.astimezone(utc)
    
  return int((utc_ts - epoch).total_seconds())
  

def main():
  config = configparser.ConfigParser()
  config.read('.secrets')
  
  esb = EsbDataCollection(config['esb']['USER'], config['esb']['PASSWORD'], config['esb']['MPRN'] )
  
  records = esb.get_json_data()
  
  logger.info('Opening InfluxDB connection...')
  try:
    client = InfluxDBClient(host=config['influx']['HOST'], port=8086, username=config['influx']['USER'], 
                            password=config['influx']['PASSWORD'], ssl=False, verify_ssl=False)
    
    client.switch_database(config['influx']['DB'])
  except Exception as e:
    logger.exception(e)
    
  logger.info('Successfully connected to %s and using database: %s' % (config['influx']['HOST'], config['influx']['DB']))
  
  points = []
  entry = {}
  for record in records:
    entry['measurement'] = 'meter_reading'
    entry['tags'] = {}
    entry['tags']['MPRN'] = record['MPRN']
    entry['tags']['MeterSerialNumber'] = record['Meter Serial Number']
    entry['tags']['ReadType'] = record['Read Type']
    entry['fields'] = {}
    entry['fields']['value'] = float(record['Read Value'])
    entry['time'] = convert_to_unix(record['Read Date and End Time'])
    points.append(deepcopy(entry))
    entry.clear()
    
  logger.info("%d records prepared for DB insertion" % len(points))
  client.write_points(points)
  

  sys.exit()
  
  



if __name__ == "__main__":
    main()