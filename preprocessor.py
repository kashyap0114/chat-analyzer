import re
import pandas as pd

def preprocess(data):
    # 1. Remove Byte Order Marks (BOM) and hidden Left-to-Right/Right-to-Left Unicode marks
    data = data.lstrip('\ufeff')
    data = re.sub(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]', '', data)
    
    # 2. Normalize invisible spaces (narrow no-break space \u202f, \xa0) to standard spaces
    data = re.sub(r'[\u202f\xa0]', ' ', data)
    
    # 3. Normalize all dash variations (en-dash, em-dash, minus) to a standard hyphen
    data = re.sub(r'[–—−]', '-', data)

    # 4. Universal Regex: Matches Android ("DD/MM/YY, HH:MM - ") AND iOS ("[DD/MM/YY, HH:MM:SS] ")
    # Handles optional am/pm, optional seconds, optional spaces, and both bracket/hyphen styles
    pattern = r'\[?\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}[,\s]+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP]\.?\s?[mM]\.?)?(?:\]|\s*-\s*)'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    # If pattern failed to match anything, return an empty DataFrame safely
    if not messages or not dates:
        return pd.DataFrame()

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Clean extracted timestamp strings (remove '[', ']', trailing hyphens, and whitespace)
    clean_dates = df['message_date'].str.replace(r'[\[\]]', '', regex=True)
    clean_dates = clean_dates.str.replace(r'\s*-\s*$', '', regex=True).str.strip()

    # Flexibly parse datetimes (dayfirst=True handles Indian DD/MM/YYYY formatting perfectly)
    try:
        df['date'] = pd.to_datetime(clean_dates, format='mixed', dayfirst=True)
    except (TypeError, ValueError):
        # Fallback for older Pandas versions
        df['date'] = pd.to_datetime(clean_dates, dayfirst=True, errors='coerce')

    # If dayfirst parsing failed across the board, try standard parsing
    if df['date'].isna().all():
        df['date'] = pd.to_datetime(clean_dates, errors='coerce')

    # Drop rows where date parsing completely failed or message is empty
    df = df.dropna(subset=['date', 'user_message'])

    users = []
    messages = []
    for message in df['user_message']:
        # Split cleanly on the first ": " to guarantee ALL group members are captured correctly
        if ': ' in str(message):
            entry = str(message).split(': ', 1)
            users.append(entry[0].strip())
            messages.append(entry[1].strip())
        else:
            users.append('group_notification')
            messages.append(str(message).strip())

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message', 'message_date'], inplace=True)

    # Force string type to prevent floating-point AttributeError crashes in WordCloud
    df['message'] = df['message'].astype(str)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-00")
        elif hour == 0:
            period.append(f"00-{hour + 1}")
        else:
            period.append(f"{hour}-{hour + 1}")

    df['period'] = period

    return df