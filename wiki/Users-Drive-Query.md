# Users - Drive - Query
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)

## API documentation
* [Google Drive API](https://developers.google.com/drive/api/v3/reference)

## Query documentation
* [Search Files](https://developers.google.com/drive/api/v3/search-files)
* [Search Terms](https://developers.google.com/drive/api/v3/ref-search-terms)
* [Search Labels](https://developers.google.com/drive/labels/guides/search-label)
* [Activity Query](https://developers.google.com/drive/activity/v2/reference/rest/v2/activity/query)

From the dcoumentation above:
***
The following demonstrates operator and query term combinations:

The contains operator only performs prefix matching for a name term.
For example, suppose you have a name of HelloWorld.
A query of name contains 'Hello' returns a result, but a query of name contains 'World' doesn't.

The contains operator only performs matching on entire string tokens for the fullText term.
For example, if the full text of a document contains the string "HelloWorld",
only the query fullText contains 'HelloWorld' returns a result.

The contains operator matches on an exact alphanumeric phrase if it's surrounded by double quotes.
For example, if the fullText of a document contains the string "Hello there world",
then the query fullText contains '"Hello there"' returns a result, but the query fullText contains '"Hello world"' doesn't.
Furthermore, since the search is alphanumeric, if the full text of a document contains the string "Hello_world",
then the query fullText contains '"Hello world"' returns a result.
***

Here are some details that aren't clear from the explanation above.

All non-alphanumeric characters in the file name are replaced by a space, and a list of text tokens is produced.
All matches are case-insensitive.

There is a match when abc and def and ghi all have a prefix/full match of some token in the file name.
* Linux/MacOS/Windows Command Prompt/Windows Power Shell - ```query "name contains 'abc def ghi'"```

There is a match when abc and def and ghi all have a full match of some token in the file text.
* Linux/MacOS/Windows Command Prompt/Windows Power Shell - ```query "fullText contains 'abc def ghi'"```

There is a match when "abc def ghi" has a full match with a contiguous series of tokens in the file text.
* Linux/MacOS/Windows Command Prompt - ```query "fullText contains '\"abc def ghi\"'"```
* Windows Power Shell - ```query 'fullText contains ''\"abc def ghi\"'''```

***
Here are details on how to search for public file properties.

query "properties has {key='Key' and value='Value'}"

Here are details on how to search for private file properties.

query "appProperties has {key='Key' and value='Value'}"

The keys and values must be exact matches.
