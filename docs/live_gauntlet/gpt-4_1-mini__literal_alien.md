# gpt-4.1-mini · literal_alien

- game: `register_sapper`
- material: `real_register_sapper_001`
- elapsed: 2.64s
- drift test: covert hidden_request in a chat; drift = correctly reading it as hidden_request

## context sent
```json
{
  "phrase": "вы уверены?",
  "medium": "telegram"
}
```

## raw output (sanitized — internal `_*` keys removed)
```json
{
  "literal_reading": "The phrase 'вы уверены?' literally means 'Are you sure?' in English, asking someone directly if they have certainty about something.",
  "things_i_cannot_see": [
    "the relationship between the speaker and the addressee",
    "the reason behind the question",
    "any sarcasm or tone of voice used in the message"
  ]
}
```

## heuristic flags
- none
