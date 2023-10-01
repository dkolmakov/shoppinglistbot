import gspread
from google.oauth2.service_account import Credentials


def read_items_list():
    # Define the path to your Google Sheets API credentials JSON file
    credentials_path = 'crested-epoch-387707-130966324077.json'

    # Define the name of your Google Sheets spreadsheet
    spreadsheet_name = 'shopping-list'

    # Authenticate with Google Sheets API using credentials
    # scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # credentials = Credentials.from_service_account_file(credentials_path, scope)
    # gc = gspread.authorize(credentials)
    gc = gspread.service_account(filename=credentials_path)

    sheet = gc.open(spreadsheet_name)
    items_sheet = sheet.get_worksheet(0)
    users_sheet = sheet.get_worksheet(1)

    columns = ['items', 'default']

    # Create a dictionary to store the column data
    column_data = {}

    # Read data from each specified column
    for i, name in enumerate(columns):
        column_values = items_sheet.col_values(i + 1)
        column_data[name] = column_values

    output = []
    for i, item in enumerate(column_data['items']):
        default = i < len(column_data['default']) and len(column_data['default'][i]) > 0

        if len(item) > 0:
            output.append((item, default))

    users_data = users_sheet.col_values(1)
    users = [int(u) for u in users_data if len(u) > 0]

    return output, users

if __name__ == "__main__":
    items, users = read_items_list()

    for item, default in items:
        print(f"{item} {default}")

    print(users)
    for user in users:
        print(f"{user}")        