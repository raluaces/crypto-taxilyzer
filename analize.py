#!/usr/bin/env python

import csv
fills = []
balances = {'LTC': 0, 'BTC': 0, 'BCH': 0, 'ETH': 0}
np_buys = []
csv_path = '/path/to/csv'

print('##########STARTING RUN##########')
with open(csv_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
            fixed_row = []
            for item in row:
                fixed_row.append(item.replace(' ', '_'))
            column_titles = fixed_row
            continue
        else:
            line_count += 1
            col = 0
            fill = dict()
            for item in column_titles:
                fill[item] = row[col]
                col += 1
            fills.append(fill)

fills.sort(key=lambda item:item['created_at'])

print(fills)

pfills = dict()
nonproc_buys = dict()
for row in fills:
    pfills[row['trade_id']] = {
        'currency': row['size_unit'],
        'size': float(row['size']),
        'date': row['created_at'],
        'price': float(row['price']),
        'side': row['side'],
        'total': float(row['total'])
    }
    # stick our buys into a separate dict to handle later
    if row['side'] == 'BUY':
        nonproc_buys[row['trade_id']] = pfills[row['trade_id']]

delete_these_buys = []
taxable_data = dict()
for key, value in pfills.items():
    print(key, value)
    if value['side'] == 'BUY':
        balances[value['currency']] = balances[value['currency']] + value['size']
    if value['side'] == 'SELL':
        balances[value['currency']] = balances[value['currency']] - value['size']
        sell_size = value['size']

        for buy_id, buy_data in nonproc_buys.items():
            remainder = buy_data['size'] - sell_size
            buy_size_at_start = buy_data['size']
            if round(remainder, 2) > 0:
                print('Left over from in original purchase {}, adding back'.format(buy_id))
                nonproc_buys[buy_id]['size'] = remainder
                nonproc_buys[buy_id]['total'] = remainder * nonproc_buys[buy_id]['price'] * -1
                print('Updated: {}'.format(nonproc_buys[buy_id]))
                cost_basis = (buy_data['price'] * sell_size)
                transaction_size = value['size']
            else:
                cost_basis = (buy_data['price'] * buy_data['size'])
                print('Removing buy {} from processed buys'.format(buy_id))
                delete_these_buys.append(buy_id)
                transaction_size = buy_data['size']

            proceeds = (value['price'] * transaction_size)

            reported_income = proceeds - cost_basis

            ####### PRINT OUT OUR TAX SHIT HERE ############
            print('#################SALE##################')
            print('SELL ID: {}'.format(key))
            print('(1b) Purchase Date: {}'.format(buy_data['date']))
            print('(1c) Sell Date: {}'.format(value['date']))
            print('(1d) Proceeds: {}'.format(proceeds))
            print('(1e) Cost Basis: {}'.format(cost_basis))
            print('(N/A) Reported Income: {}'.format(reported_income))
            print('#######################################')
            ################################################

            taxable_data[key] = {
                'currency': value['currency'],
                'purchase_date': buy_data['date'],
                'sell_date': value['date'],
                'proceeds': proceeds,
                'cost_basis': cost_basis
            }

            # subtract the size of coins we calculated for above
            sell_size = sell_size - buy_size_at_start

            print('Remaining funds in sale: {}'.format(sell_size))
            if round(sell_size, 2) <= 0:
                break

        if delete_these_buys:
            for buy in delete_these_buys:
                nonproc_buys.pop(buy)
            delete_these_buys = []

with open('output.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    row_titles = ['Currency Name', 'Purchase Date', 'Cost Basis', 'Date sold', 'Proceeds']
    writer.writerow(row_titles)
    for key, value in taxable_data.items():
        ## we need to deliver this...
        ## Currency Name, Purchase Date, Cost Basis, Date sold, and Proceeds, then try uploading it again.
        row = [value['currency'], value['purchase_date'], value['cost_basis'], value['sell_date'], value['proceeds']]
        writer.writerow(row)

file.close()

print('Finished!')
print(balances)
