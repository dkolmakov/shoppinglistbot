import codecs

def read_items_list():
    items_file = codecs.open("items.list", encoding='utf-8')
    users_file = open("users.list")

    users = [int(u) for u in users_file if len(u) > 0]
    output = [(i.strip(), False) for i in items_file if len(i.strip()) > 0]

    return output, users

if __name__ == "__main__":
    items, users = read_items_list()

    for item, default in items:
        print(f"{item} {default}")

    print(users)
    for user in users:
        print(f"{user}")       
