"""Methods related to display of information to the user."""

import csv
import datetime
import io
import sys
import webbrowser

import dateutil
import googleapiclient.http

#TODO: get rid of these hacks
import __main__
from var import *
import controlflow
import gapi


def current_count(i, count):
  return f' ({i}/{count})' if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else ''

def current_count_nl(i, count):
  return f' ({i}/{count})\n' if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else '\n'

def add_field_to_fields_list(fieldName, fieldsChoiceMap, fieldsList):
  fields = fieldsChoiceMap[fieldName.lower()]
  if isinstance(fields, list):
    fieldsList.extend(fields)
  else:
    fieldsList.append(fields)

# Write a CSV file
def add_titles_to_csv_file(addTitles, titles):
  for title in addTitles:
    if title not in titles:
      titles.append(title)

def add_row_titles_to_csv_file(row, csvRows, titles):
  csvRows.append(row)
  for title in row:
    if title not in titles:
      titles.append(title)

# fieldName is command line argument
# fieldNameMap maps fieldName to API field names; CSV file header will be API field name
#ARGUMENT_TO_PROPERTY_MAP = {
#  u'admincreated': [u'adminCreated'],
#  u'aliases': [u'aliases', u'nonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def add_field_to_csv_file(fieldName, fieldNameMap, fieldsList, fieldsTitles, titles):
  for ftList in fieldNameMap[fieldName]:
    if ftList not in fieldsTitles:
      fieldsList.append(ftList)
      fieldsTitles[ftList] = ftList
      add_titles_to_csv_file([ftList], titles)

# fieldName is command line argument
# fieldNameTitleMap maps fieldName to API field name and CSV file header
#ARGUMENT_TO_PROPERTY_TITLE_MAP = {
#  u'admincreated': [u'adminCreated', u'Admin_Created'],
#  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def add_field_title_to_csv_file(fieldName, fieldNameTitleMap, fieldsList, fieldsTitles, titles):
  ftList = fieldNameTitleMap[fieldName]
  for i in range(0, len(ftList), 2):
    if ftList[i] not in fieldsTitles:
      fieldsList.append(ftList[i])
      fieldsTitles[ftList[i]] = ftList[i+1]
      add_titles_to_csv_file([ftList[i+1]], titles)

def sort_csv_titles(firstTitle, titles):
  restoreTitles = []
  for title in firstTitle:
    if title in titles:
      titles.remove(title)
      restoreTitles.append(title)
  titles.sort()
  for title in restoreTitles[::-1]:
    titles.insert(0, title)

def QuotedArgumentList(items):
  return ' '.join([item if item and (item.find(' ') == -1) and (item.find(',') == -1) else '"'+item+'"' for item in items])

def write_csv_file(csvRows, titles, list_type, todrive):
  def rowDateTimeFilterMatch(dateMode, rowDate, op, filterDate):
    if not rowDate or not isinstance(rowDate, str):
      return False
    try:
      rowTime = dateutil.parser.parse(rowDate, ignoretz=True)
      if dateMode:
        rowDate = datetime.datetime(rowTime.year, rowTime.month, rowTime.day).isoformat()+'Z'
    except ValueError:
      rowDate = NEVER_TIME
    if op == '<':
      return rowDate < filterDate
    if op == '<=':
      return rowDate <= filterDate
    if op == '>':
      return rowDate > filterDate
    if op == '>=':
      return rowDate >= filterDate
    if op == '!=':
      return rowDate != filterDate
    return rowDate == filterDate

  def rowCountFilterMatch(rowCount, op, filterCount):
    if isinstance(rowCount, str):
      if not rowCount.isdigit():
        return False
      rowCount = int(rowCount)
    elif not isinstance(rowCount, int):
      return False
    if op == '<':
      return rowCount < filterCount
    if op == '<=':
      return rowCount <= filterCount
    if op == '>':
      return rowCount > filterCount
    if op == '>=':
      return rowCount >= filterCount
    if op == '!=':
      return rowCount != filterCount
    return rowCount == filterCount
  def rowBooleanFilterMatch(rowBoolean, filterBoolean):
    if not isinstance(rowBoolean, bool):
      return False
    return rowBoolean == filterBoolean

  def headerFilterMatch(filters, title):
    for filterStr in filters:
      if filterStr.match(title):
        return True
    return False

  if GC_Values[GC_CSV_ROW_FILTER]:
    for column, filterVal in iter(GC_Values[GC_CSV_ROW_FILTER].items()):
      if column not in titles:
        sys.stderr.write(f'WARNING: Row filter column "{column}" is not in output columns\n')
        continue
      if filterVal[0] == 'regex':
        csvRows = [row for row in csvRows if filterVal[1].search(str(row.get(column, '')))]
      elif filterVal[0] == 'notregex':
        csvRows = [row for row in csvRows if not filterVal[1].search(str(row.get(column, '')))]
      elif filterVal[0] in ['date', 'time']:
        csvRows = [row for row in csvRows if rowDateTimeFilterMatch(filterVal[0] == 'date', row.get(column, ''), filterVal[1], filterVal[2])]
      elif filterVal[0] == 'count':
        csvRows = [row for row in csvRows if rowCountFilterMatch(row.get(column, 0), filterVal[1], filterVal[2])]
      else: #boolean
        csvRows = [row for row in csvRows if rowBooleanFilterMatch(row.get(column, False), filterVal[1])]
  if GC_Values[GC_CSV_HEADER_FILTER] or GC_Values[GC_CSV_HEADER_DROP_FILTER]:
    if GC_Values[GC_CSV_HEADER_DROP_FILTER]:
      titles = [t for t in titles if not headerFilterMatch(GC_Values[GC_CSV_HEADER_DROP_FILTER], t)]
    if GC_Values[GC_CSV_HEADER_FILTER]:
      titles = [t for t in titles if headerFilterMatch(GC_Values[GC_CSV_HEADER_FILTER], t)]
    if not titles:
      controlflow.system_error_exit(3, 'No columns selected with GAM_CSV_HEADER_FILTER and GAM_CSV_HEADER_DROP_FILTER\n')
      return
  csv.register_dialect('nixstdout', lineterminator='\n')
  if todrive:
    write_to = io.StringIO()
  else:
    write_to = sys.stdout
  writer = csv.DictWriter(write_to, fieldnames=titles, dialect='nixstdout', extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
  try:
    writer.writerow(dict((item, item) for item in writer.fieldnames))
    writer.writerows(csvRows)
  except IOError as e:
    controlflow.system_error_exit(6, e)
  if todrive:
    admin_email = __main__._getValueFromOAuth('email')
    _, drive = __main__.buildDrive3GAPIObject(admin_email)
    if not drive:
      print(f'''\nGAM is not authorized to create Drive files. Please run:
gam user {admin_email} check serviceaccount
and follow recommend steps to authorize GAM for Drive access.''')
      sys.exit(5)
    result = gapi.call(drive.about(), 'get', fields='maxImportSizes')
    columns = len(titles)
    rows = len(csvRows)
    cell_count = rows * columns
    data_size = len(write_to.getvalue())
    max_sheet_bytes = int(result['maxImportSizes'][MIMETYPE_GA_SPREADSHEET])
    if cell_count > MAX_GOOGLE_SHEET_CELLS or data_size > max_sheet_bytes:
      print(f'{WARNING_PREFIX}{MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET}')
      mimeType = 'text/csv'
    else:
      mimeType = MIMETYPE_GA_SPREADSHEET
    body = {'description': QuotedArgumentList(sys.argv),
            'name': f'{GC_Values[GC_DOMAIN]} - {list_type}',
            'mimeType': mimeType}
    result = gapi.call(drive.files(), 'create', fields='webViewLink',
                       body=body,
                       media_body=googleapiclient.http.MediaInMemoryUpload(write_to.getvalue().encode(),
                                                                           mimetype='text/csv'))
    file_url = result['webViewLink']
    if GC_Values[GC_NO_BROWSER]:
      msg_txt = f'Drive file uploaded to:\n {file_url}'
      msg_subj = f'{GC_Values[GC_DOMAIN]} - {list_type}'
      __main__.send_email(msg_subj, msg_txt)
      print(msg_txt)
    else:
      webbrowser.open(file_url)

def print_error(message):
  """Prints a one-line error message to stderr in a standard format."""
  sys.stderr.write('\n{0}{1}\n'.format(ERROR_PREFIX, message))


def print_warning(message):
  """Prints a one-line warning message to stderr in a standard format."""
  sys.stderr.write('\n{0}{1}\n'.format(WARNING_PREFIX, message))

def print_json(object_value, spacing=''):
  """Prints Dict or Array to screen in clean human-readable format.."""
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, int, bool)):
      sys.stdout.write(f'{object_value[0]}\n')
      return
    if spacing:
      sys.stdout.write('\n')
    for i, a_value in enumerate(object_value):
      if isinstance(a_value, (str, int, bool)):
        sys.stdout.write(f' {spacing}{i+1}) {a_value}\n')
      else:
        sys.stdout.write(f' {spacing}{i+1}) ')
        print_json(a_value, f' {spacing}')
  elif isinstance(object_value, dict):
    for key in ['kind', 'etag', 'etags']:
      object_value.pop(key, None)
    for another_object, another_value in object_value.items():
      sys.stdout.write(f' {spacing}{another_object}: ')
      print_json(another_value, f' {spacing}')
  else:
    sys.stdout.write(f'{object_value}\n')
