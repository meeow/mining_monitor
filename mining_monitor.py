#Author: Brandon Hong
#hongbrandon at(@) gmail | byhong at(@) andrew d0t cmu d()t edu

#Dwarfpool mining monitor - v0.1 alpha

import urllib.request, urllib.parse, time, turtle, timeit

def get_user_info():
    currency_type = input("Enter currency type (zec or eth): ")
    while currency_type not in {"zec", "eth"}:
        print("Error: Please try again.")
        currency_type = input("Enter currency type (zec or eth): ")


    wallet_address = input("Wallet address: ")
    while len(wallet_address) != len("t1ZZJdjbkjA4TxTmbYYxQZwxKxNR6efvDB4") and currency_type == "zec":
        if wallet_address != "":
            print("Error: Please try again.")
        wallet_address = input("Wallet address: ")

    refresh_rate = int(input("Refresh rate in seconds (min: 10): "))
    while refresh_rate < 10:
        print("Error: Please try again.")
        refresh_rate = int(input("Refresh rate in seconds (min: 10): "))

    enable_gui = input("Enable graphics? (y/n): ")

    if enable_gui == 'y': 
        enable_gui = True
    else:
        enable_gui = False

    url = user_info_to_url(currency_type, wallet_address)

    return url, refresh_rate, enable_gui, currency_type

def user_info_to_url(currency_type, wallet_address):
    dwarfpool_url = "https://dwarfpool.com/" + currency_type + "/address?wallet=" + wallet_address
    return dwarfpool_url

def get_currency_price(currency_type):
    url = ''
    if currency_type == "zec":
        url = "https://api.coinmarketcap.com/v1/ticker/zcash/"
    elif currency_type == "eth":
        url = "https://api.coinmarketcap.com/v1/ticker/ethereum/"
    webpage_as_string = url_to_string(url)
    price_index = webpage_as_string.find("price_usd")
    webpage_as_string = webpage_as_string[price_index:]
    webpage_as_string = webpage_as_string[:webpage_as_string.find('\n')]
    price = round(float(''.join([i for i in webpage_as_string if i in '1234567890.'])), 2)
    return price

def url_to_string(url):
    webpage, headers = urllib.request.urlretrieve(url)
    webpage_as_string = open(webpage).read()
    return webpage_as_string

def string_to_worker_info(url_as_string):
    worker_info = url_as_string.split("tbody>\n")[3]
    worker_info = worker_info.split("\n")
    workers = ""
    prev_line = ""

    for line in worker_info:
        if '<td class=' in line[:11] and prev_line is not "":
            workers = (workers  
                      + " "  
                      + prev_line[prev_line.find(".") + 1:prev_line.find("</")]
                      + ": "
                      + line[line.find(">") + 1:line.find("</")])

        prev_line = ""
        if "<tr><td>" in line[:9]:
            prev_line = line

    worker_info = workers.split("  ")[1:]
    return worker_info

def dictionize_worker_info(worker_info):
    worker_dict = dict()

    for worker in worker_info:
        worker = worker.split(": ")
        if ("calc" not in worker[1]):
            worker[1] = str(''.join([i for i in worker[1] if i in "0123456789."]))
            worker_dict[worker[0]] = round(float(worker[1]), 2)

    return worker_dict

#@param num_cycles: number of times that average was previously calculated
#@param prev_avg: stats for previous avg calculation
def calculate_average(refresh_rate, num_cycles, worker_info, prev_avg):
    worker_count = len(worker_info.keys())
    worker_avg = dict()

    if prev_avg != dict():
        for key in prev_avg.keys():
            worker_avg[key] = round((prev_avg[key] * num_cycles + worker_info[key])/(num_cycles + 1), 2)
    else:
        for key in worker_info.keys():
            worker_avg[key] = worker_info[key]
    return worker_avg

def calculate_sum(worker_dict):
    total = 0
    for key in worker_dict:
        total += worker_dict[key]
    return round(total, 2)

def calculate_time(cycles, refresh_rate, seconds_offset):
    seconds = round(cycles * refresh_rate - refresh_rate + seconds_offset, 2)

    minutes = seconds // 60
    seconds = seconds % 60

    hours = minutes // 60
    minutes = minutes % 60

    days = hours // 24
    hours = hours % 24

    return (seconds, minutes, hours, days)

def rotate_turtles(turtle_list, num_turtles):
    turtle_no = 0
    angle = 360/num_turtles

    for turtle in turtle_list:

        if turtle.color()[0] == "black":
            turtle.color("red") 
        else:
            turtle.color("black")

        turtle.penup()
        turtle.home()
        turtle.pendown()
        turtle.right(angle * turtle_no)
        turtle_no += 1

def move_turtles(turtle_list, worker_info, ratio):
    count = 0
    worker_keys = list(worker_info.keys())

    for turtle in turtle_list:
        turtle.forward(worker_info[worker_keys[count]]/ratio)
        turtle.write(worker_keys[count] + " (" + str(worker_info[worker_keys[count]]) + "h/s) ", 
            move=False, 
            align="left", 
            font=("Arial", 8, "normal"))
        count += 1

def repos_avg_turtles(avg_list):
    for turtle in avg_list:
        turtle.penup()
        turtle.setpos(300, -300)
        turtle.pendown()

def draw_gui(num_workers):
    gui_window = turtle.Screen()
    turtle_list = [turtle.Turtle() for i in range(num_workers)]
    avg_list = [turtle.Turtle() for i in range(num_workers)]
    return turtle_list, avg_list

def refresh_gui(num_workers, turtle_list, avg_list, worker_info):
    rotate_turtles(turtle_list, num_workers)
    move_turtles(turtle_list, worker_info, 5)

    rotate_turtles(avg_list, num_workers)
    repos_avg_turtles(avg_list)
    move_turtles(avg_list, worker_info, 10)

def main():
    print('''-------------------------------------
Dwarfpool mining monitor - v0.1 alpha
-------------------------------------''')
    cycles = 1
    worker_avg = dict()
    url, refresh_rate, is_gui_enabled, currency_type = get_user_info()
    url_as_string = url_to_string(url)
    worker_info = string_to_worker_info(url_as_string)
    worker_info = dictionize_worker_info(worker_info)
    num_workers = len(worker_info.keys())
    turtle_list, avg_list = list(), list()
    seconds_offset = 0
    max_price = 0
    min_price = 9999999
    is_gui_drawn = False

    avg_price = get_currency_price(currency_type)

    while True:

        print("_______________________________________________________________")

        # Miner data
        print("Note: Refreshing miners html data...")
        miners_refresh_time = time.clock()
        url_as_string = url_to_string(url)
        worker_info = string_to_worker_info(url_as_string)
        worker_info = dictionize_worker_info(worker_info)
        worker_avg = calculate_average(refresh_rate, cycles, worker_info, worker_avg)
        worker_sum = calculate_sum(worker_info)
        avg_sum = calculate_sum(worker_avg)
        miners_refresh_time = round(time.clock() - miners_refresh_time, 2)
        print("    miner data refreshed in", miners_refresh_time, "s.")
        seconds_offset += miners_refresh_time

        # Price data
        print("Note: Refreshing coin price html data...")
        price_refresh_time = time.clock()
        currency_price = get_currency_price(currency_type)
        if currency_price > max_price: 
            max_price = currency_price
        if currency_price < min_price:
            min_price = currency_price
        avg_price = round((avg_price * cycles + currency_price)/(cycles + 1), 2)
        price_refresh_time = round(time.clock() - price_refresh_time, 2)
        print("    price data refreshed in", price_refresh_time, "s.")
        seconds_offset += price_refresh_time

        # Graphics data
        if is_gui_enabled:
            graph_refresh_time = time.clock()
            print("Note: Refreshing graph...")
            if not is_gui_drawn:
                turtle_list, avg_list = draw_gui(num_workers)
                is_gui_drawn = True
            refresh_gui(num_workers, turtle_list, avg_list, worker_info)
            graph_refresh_time = round(time.clock() - graph_refresh_time, 2)
            print("    graph refreshed in", graph_refresh_time, "s.")
            seconds_offset += graph_refresh_time

        # Refresh output
        seconds, minutes, hours, days = calculate_time(cycles, refresh_rate, seconds_offset)
        seconds = round(seconds, 2)

        print("_______________________________________________________________")
        print("elapsed time (approx): ", days, "d, ", hours, "h, ", minutes, "m, ", seconds, "s ")
        print("current individual hashrate: ", worker_info)
        print("average individual hashrate: ", worker_avg)
        print("current combined hashrate: ", worker_sum, "sol/s")
        print("average combined hashrate: ", avg_sum, "sol/s")
        print("current price: $", currency_price, "/" + currency_type)
        print("average price: $", avg_price,  "/" + currency_type)
        print("max price: $", max_price, "/" + currency_type)
        print("min price: $", min_price, "/" + currency_type)


        cycles += 1

        time.sleep(refresh_rate)

main()


