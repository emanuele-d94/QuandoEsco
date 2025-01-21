from datetime import datetime, timedelta, time

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from MyApp.forms import Ingresso, RegisterForm, LoginForm, GiornataForm, ModificaGiornataForm
from MyApp.models import Giornata, Turno


# Create your views here.
def registrazione(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'registrazione.html', {'form': form})

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, 'Registrazione completata correttamente!')
            login(request, user)
            return redirect('homepage')
        else:
            return render(request, 'registrazione.html', {'form': form})


def sign_in(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    elif request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('homepage')

        # form is not valid or user is not authenticated
        messages.error(request, f'Username o password non validi')
        return render(request, 'login.html', {'form': form})

def sign_out(request):
    logout(request)
    messages.warning(request,f'Utente disconnesso correttamente.')
    return redirect('login')

@login_required()
def homepage(request):
    # Ottieni l'utente loggato
    user = request.user

    # Recupera le ultime 5 giornate dell'utente in ordine cronologico discendente
    giornate = Giornata.objects.filter(user=user).order_by('-data')[:5]

    # Passa le giornate al template
    return render(request, 'homepage.html', {
        'user': user,
        'giornate': giornate,
    })

@login_required
def calcola_uscita(request):
    # Ottieni l'utente loggato
    user = request.user

    # Ottieni il turno dell'utente o crea un nuovo oggetto se non esiste
    turno, created = Turno.objects.get_or_create(user=user)
    print(turno)
    print(created)
    initial_data = {
        'durata_turno_ore': turno.ore_lavoro,
        'durata_turno_minuti': turno.minuti_lavoro,
        'durata_pausa_minuti': turno.minuti_pausa,
    }

    data_uscita = datetime.now()
    messaggio_info = "Compila il form e premi il pulsante \'Quando Esco?\'"
    messaggio_success = None
    messaggio_danger = None
    messaggio_warning = None
    messaggio_save_success = None
    messaggio_save_warning = None
    scroll_to_bottom = False

    if request.method == 'POST':
        form = Ingresso(request.POST)
        if form.is_valid():
            durata_turno_ore = form.cleaned_data['durata_turno_ore']
            durata_turno_minuti = form.cleaned_data['durata_turno_minuti']
            data_ingresso = form.cleaned_data['ingresso']
            minuti_pausa = form.cleaned_data['durata_pausa_minuti']

            print("Durata turno ore:", durata_turno_ore)
            print("Durata turno minuti:", durata_turno_minuti)
            print("Durata pausa minuti:", minuti_pausa)

            durata = timedelta(hours=durata_turno_ore, minutes=durata_turno_minuti + minuti_pausa)
            data_uscita = data_ingresso + durata

            print("Ingresso: ", data_ingresso)
            print("Uscita: ", data_uscita)

            now = datetime.now()

            print("Now: ", now)
            # Converto uscita e now in timestamp
            now_timestamp = now.timestamp()
            data_uscita_timestamp = data_uscita.timestamp()
            #Differenza in minuti:
            differenza_minuti = (data_uscita_timestamp  - now_timestamp) / 60
            #differenza_minuti -= 60
            print("Differenza minuti: ", differenza_minuti)

            if differenza_minuti <= 0:
                messaggio_success = "Cosa fai ancora qui? E' ora di andare a casa!"
                messaggio_info = None
                messaggio_danger = None
                messaggio_warning = None
            elif 0 < differenza_minuti <= 60:
                messaggio_success = "Manca poco, tieni duro!"
                messaggio_info = None
                messaggio_danger = None
                messaggio_warning = None
            elif 60 < differenza_minuti <= 240:
                messaggio_warning = "Ne hai ancora per un pò, buon lavoro!"
                messaggio_success = None
                messaggio_info = None
                messaggio_danger = None
            else:
                messaggio_danger = "La giornata è ancora lunga, datti da fare!"
                messaggio_warning = None
                messaggio_success = None
                messaggio_info = None

            scroll_to_bottom = True

            # Aggiorno il Turno dell'utente
            turno.ore_lavoro = durata_turno_ore
            turno.minuti_lavoro = durata_turno_minuti
            turno.minuti_pausa = minuti_pausa
            turno.save()

            # Creo e salvo la giornata se non esiste

            giornata = Giornata.objects.filter(user=user,data=data_ingresso).first()
            if giornata:
                messaggio_save_warning = f"Giornata {giornata.data.strftime('%d-%m-%Y')} già presente nel Registro."
            else:
                giornata = Giornata()
                giornata.user = request.user
                giornata.data = data_ingresso
                print(giornata.data)
                giornata.ingresso = time(
                    hour=data_ingresso.hour,
                    minute=data_ingresso.minute
                )
                giornata.uscita = time(
                    hour=data_uscita.hour,
                    minute=data_uscita.minute
                )
                print(giornata)
                giornata.ore_lavorate = durata_turno_ore
                giornata.minuti_lavorati = durata_turno_minuti
                giornata.minuti_pausa = minuti_pausa
                giornata.save()
                messaggio_save_success = f"Giornata {giornata.data.strftime('%d-%m-%Y')} salvata nel Registro!"

    else:
        print('Form non popolato')
        form = Ingresso(initial=initial_data)

    return render(request,
                  'calcola_uscita.html',
                  { 'form': form,
                            'uscita': data_uscita,
                            'messaggio_info': messaggio_info,
                            'messaggio_warning':messaggio_warning,
                            'messaggio_danger': messaggio_danger,
                            'messaggio_success': messaggio_success,
                            'messaggio_save_success': messaggio_save_success,
                            'messaggio_save_warning': messaggio_save_warning,
                            'scroll_to_bottom': scroll_to_bottom,  # Variabile per trigger dello scroll
                    })

@login_required()
def salva_giornata(request):
    if request.method == 'GET':
        print('GET')
        context = {'form': GiornataForm()}
        return render(request, 'salva_giornata.html', context)
    elif request.method == 'POST':
        print('POST')
        form = GiornataForm(request.POST)
        if form.is_valid():
            print('FORM VALID')
            # Controlla se esiste già un record per l'utente e la data
            user = request.user
            data = form.cleaned_data['data']
            if Giornata.objects.filter(user=user, data=data).exists():
                messages.error(request, f"Esiste già un record per il giorno {data}!")
                return redirect('salva_giornata')  # Ritorna al form con l'errore

            # Aggiunge l'utente user presente nella request all'oggetto giornata prima di salvarlo
            giornata = form.save(commit=False)  # Non salvare ancora nel database
            # calcolo ore di lavoro
            ingresso = form.cleaned_data['ingresso']
            uscita = form.cleaned_data['uscita']
            minuti_pausa = form.cleaned_data['minuti_pausa']

            # Crea due oggetti datetime combinando la data con i time
            ingresso_datetime = datetime.combine(data, ingresso)
            uscita_datetime = datetime.combine(data, uscita)

            #uscita deve essere successiva a ingresso
            # Verifica se l'uscita è successiva all'ingresso
            if uscita_datetime <= ingresso_datetime:
                print("Errore: l'uscita deve essere successiva all'ingresso!")
                messages.warning(request, f"Errore: l'uscita deve essere successiva all'ingresso.")
                return render(request, 'salva_giornata.html', {'form': form})

            # Calcola la differenza in minuti totali
            differenza_minuti = int((uscita_datetime - ingresso_datetime).total_seconds() / 60)

            # Sottrai i minuti di pausa
            differenza_effettiva_minuti = differenza_minuti - minuti_pausa

            #la differenza in minuti tra uscita e ingresso deve essere maggiore dei minuti di pausa
            if differenza_effettiva_minuti <=0:
                print("Errore: la pausa non può durare più del turno di lavoro!.")
                messages.warning(request, f"Errore: la pausa non può durare più del turno di lavoro!")
                return render(request, 'salva_giornata.html', {'form': form})

            # Calcola ore e minuti
            ore_lavorate, minuti_lavorati = divmod(differenza_effettiva_minuti, 60)

            print(f"Differenza effettiva: {ore_lavorate} ore e {minuti_lavorati} minuti")

            giornata.user = request.user  # Assegna l'utente loggato
            giornata.ore_lavorate = ore_lavorate
            giornata.minuti_lavorati = minuti_lavorati
            giornata.save()  # Salva l'oggetto con l'utente
            messages.success(request, f"Giornata di lavoro salvata per il giorno {data} ")

            return redirect('registro')
        else:
            print('FORM NOT VALID')
            print(form.errors)  # Stampa errori di validazione per debug
            messages.warning(request, f"Form non valido!")
            return render(request, 'salva_giornata.html', {'form': form})

@login_required()
def registro(request):
    # Ottieni l'utente loggato
    user = request.user

    # Elenco mesi (1-12) con i loro nomi
    mesi = [
        (1, "Gennaio"), (2, "Febbraio"), (3, "Marzo"), (4, "Aprile"),
        (5, "Maggio"), (6, "Giugno"), (7, "Luglio"), (8, "Agosto"),
        (9, "Settembre"), (10, "Ottobre"), (11, "Novembre"), (12, "Dicembre")
    ]
    # Anni disponibili nel database
    # Estrazione anni disponibili
    anni_disponibili = Giornata.objects.filter(user=user).dates('data', 'year', order='DESC')
    anni = [anno.year for anno in anni_disponibili]
    # Parametri GET
    mese_selezionato = int(request.GET.get('mese', datetime.today().month))
    anno_selezionato = int(request.GET.get('anno', datetime.today().year))

    # Filtro giornate
    giornate = Giornata.objects.filter(
        user=user,
        data__year=anno_selezionato,
        data__month=mese_selezionato
    )

    ore_lavoro_tot = 0
    minuti_lavoro_tot = 0
    ore_pausa_tot=0
    minuti_pausa_tot=0
    # Calcolo ore totali di lavoro, minuti totali di lavoro, ore totali di pausa, minuti totali di pausa
    for giornata in giornate:
        ore_lavoro_tot += giornata.ore_lavorate
        minuti_lavoro_tot += giornata.minuti_lavorati
        minuti_pausa_tot += giornata.minuti_pausa

    ore_lavoro_tot += minuti_lavoro_tot//60
    minuti_lavoro_tot = minuti_lavoro_tot % 60

    ore_pausa_tot = minuti_pausa_tot // 60
    minuti_pausa_tot= minuti_pausa_tot % 60


    context = {
        'giornate': giornate,
        'mesi': mesi,
        'anni': anni,
        'mese_selezionato': mese_selezionato,
        'anno_selezionato': anno_selezionato,
        'ore_lavoro_tot': ore_lavoro_tot,
        'minuti_lavoro_tot': minuti_lavoro_tot,
        'ore_pausa_tot': ore_pausa_tot,
        'minuti_pausa_tot': minuti_pausa_tot
    }

    return render(request, 'registro.html', context)

@login_required()
def modifica_giornata(request,id):
    # Recupera l'oggetto Giornata associato all'utente loggato e all'id specificato
    giornata = get_object_or_404(Giornata, id=id, user=request.user)
    data = giornata.data
    initial_value = {
        'ingresso': giornata.ingresso,
        'uscita': giornata.uscita,
        'minuti_pausa': giornata.minuti_pausa
    }
    if request.method == 'GET':
        print('GET')
        context = {'data': data,
            'form': ModificaGiornataForm(initial=initial_value),}
        return render(request, 'modifica_giornata.html', context)
    elif request.method == 'POST':
        print('POST')
        form = ModificaGiornataForm(request.POST)
        if form.is_valid():
            print('FORM VALID')
            # Qui sto creando un nuovo oggetto giornata su cui andrò ad inserire i nuovi valori
            giornata = form.save(commit=False)  # Non salvare ancora nel database
            # calcolo ore di lavoro
            ingresso = form.cleaned_data['ingresso']
            uscita = form.cleaned_data['uscita']
            minuti_pausa = form.cleaned_data['minuti_pausa']

            # Crea due oggetti datetime combinando la data con i time
            ingresso_datetime = datetime.combine(data, ingresso)
            uscita_datetime = datetime.combine(data, uscita)

            #uscita deve essere successiva a ingresso
            # Verifica se l'uscita è successiva all'ingresso
            if uscita_datetime <= ingresso_datetime:
                print("Errore: l'uscita deve essere successiva all'ingresso!")
                messages.warning(request, f"Errore: l'uscita deve essere successiva all'ingresso.")
                return render(request, 'modifica_giornata.html', {'data': data,'form': form})

            # Calcola la differenza in minuti totali
            differenza_minuti = int((uscita_datetime - ingresso_datetime).total_seconds() / 60)

            # Sottrai i minuti di pausa
            differenza_effettiva_minuti = differenza_minuti - minuti_pausa

            #la differenza in minuti tra uscita e ingresso deve essere maggiore dei minuti di pausa
            if differenza_effettiva_minuti <=0:
                print("Errore: la pausa non può durare più del turno di lavoro!.")
                messages.warning(request, f"Errore: la pausa non può durare più del turno di lavoro!")
                return render(request, 'modifica_giornata.html', {'data': data,'form': form})

            # Calcola ore e minuti
            ore_lavorate, minuti_lavorati = divmod(differenza_effettiva_minuti, 60)

            print(f"Differenza effettiva: {ore_lavorate} ore e {minuti_lavorati} minuti")
            giornata.data = data  # Devo reinserire la data su giornata
            giornata.user = request.user # Devo reinserire l'user
            giornata.id = id # Devo reinserie l'id della Giornata
            giornata.ore_lavorate = ore_lavorate
            giornata.minuti_lavorati = minuti_lavorati
            giornata.save()  # Salva l'oggetto con l'utente
            messages.warning(request, f"Giornata di lavoro modificata per il giorno {data}")
            return redirect('registro')
        else:
            print('FORM NOT VALID')
            print(form.errors)  # Stampa errori di validazione per debug
            messages.warning(request, f"Form non valido!")
            return render(request, 'modifica_giornata.html', {'data': giornata.data,'form': form})

@login_required
def elimina_giornata(request, id):
    # Recupera l'oggetto Giornata
    giornata = get_object_or_404(Giornata, id=id, user=request.user)

    # Elimina la giornata
    giornata.delete()

    messages.error(request, f"Giornata di lavoro eliminata per il giorno {giornata.data}")

    return redirect('registro')  # Torna alla pagina registro dopo l'eliminazione