"""GAM user YouTube Channel commands."""

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent
from gam.util.args import getArgument, getString, getLanguageCode, BCP47_LANGUAGE_CODES_MAP
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, getFieldsList, addFieldToFieldsList

YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP = {
  'brandingsettings': 'brandingSettings',
  'contentdetails': 'contentDetails',
  'contentownerdetails': 'contentOwnerDetails',
  'id': 'id',
  'localizations': 'localizations',
  'snippet': 'snippet',
  'statistics': 'statistics',
  'status': 'status',
  'topicdetails': 'topicDetails',
  }

YOUTUBE_CHANNEL_TIME_OBJECTS = {'publishedAt'}
from gam.util.display import entityActionFailedWarning
from gam.util.entity import getEntityList

def printShowYouTubeChannel(users):
  csvPF = CSVPrintFile(['User', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {'mine': True}
  languageCode = ''
  fieldsList = ['id']
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'mine':
      kwargs = {'mine': True}
    elif myarg in {'id', 'ids', 'channel', 'channels'}:
      kwargs = {'id': ','.join(getEntityList(Cmd.OB_YOUTUBE_CHANNEL_ID_LIST))}
    elif myarg == 'forusername':
      kwargs = {'forUsername': getString(Cmd.OB_USER_NAME)}
    elif myarg == 'managedbyme':
      kwargs = {'managedByMe': True, 'onBehalfOfContentOwner': getString(Cmd.OB_USER_NAME)}
    elif getFieldsList(myarg, YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'allfields':
      for field in YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP, fieldsList)
    elif myarg in {'languagecode', 'hl'}:
      languageCode = getLanguageCode(BCP47_LANGUAGE_CODES_MAP)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  kwargs['part'] = ','.join(set(fieldsList))
  if languageCode:
    kwargs['hl'] = languageCode
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, yt = buildGAPIServiceObject(API.YOUTUBE, user, i, count)
    if not yt:
      continue
    try:
      channels = callGAPIpages(yt.channels(), 'list', 'items',
                               throwReasons=GAPI.YOUTUBE_THROW_REASONS,
                               fields='nextPageToken,items', **kwargs)
    except (GAPI.unsupportedSupervisedAccount, GAPI.unsupportedLanguageCode) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.contentOwnerAccountNotFound as e:
      if 'managedByMe' in kwargs:
        entityActionFailedWarning([Ent.USER, user, Ent.OWNER, kwargs['onBehalfOfContentOwner']], str(e), i, count)
      else:
        entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.authError):
      userYouTubeServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      jcount = len(channels)
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.YOUTUBE_CHANNEL, i, count)
      Ind.Increment()
      j = 0
      for channel in channels:
        j += 1
        if FJQC.formatJSON:
          printLine(json.dumps(cleanJSON(channel, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS),
                               ensure_ascii=False, sort_keys=True))
          break
        printEntity([Ent.YOUTUBE_CHANNEL, channel['id']], j, jcount)
        Ind.Increment()
        showJSON(None, channel, skipObjects={'id'}, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS)
        Ind.Decrement()
      Ind.Decrement()
    elif channels:
      for channel in channels:
        row = {'User': user, 'id': channel['id']}
        flattenJSON(channel, flattened=row, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'User': user, 'id': channel['id'],
                 'JSON': json.dumps(cleanJSON(channel, timeObjects=YOUTUBE_CHANNEL_TIME_OBJECTS),
                                    ensure_ascii=False, sort_keys=True)}
          csvPF.WriteRowNoFilter(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('YouTube Channels')
