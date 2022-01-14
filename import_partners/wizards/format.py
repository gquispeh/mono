# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def format_tel(num):
    pass


def format_name(name, method='default', no_caps=['DE', 'DELS']):
    # No spaces
    try:
        for i, c in enumerate(name):
            if c != ' ':
                name = name[i:]
                break

        if method == 'last':

            for e, c in enumerate(name[::-1]):
                if not c.isdigit() and c != ' ':
                    if e != 0:
                        name = name[:-e]
                    break

        else:
            name = ''.join([c for c in name if not c.isdigit()])
        name = name.split(' ')
        for i, e in enumerate(name):
            if e not in no_caps:
                name[i] = e.capitalize()
            else:
                name[i] = e.lower()
        return ' '.join(c for c in name)
    except Exception:
        return False


name_list = [
    ' AJUNTAMENT DE PLAMPLONA 5312',
    'Ajuntamnet De PamPlona ',
    'Ajuntament de Pamplona'
]

print(list(map(
    lambda x: format_name(x, method='last'), name_list))
)
