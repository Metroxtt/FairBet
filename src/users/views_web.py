from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from users.models import User


# Vista del Dashboard Principal
@login_required
def home_view(request):
    from events.models import Event
    from wallet.models import Account
    from betting.models import Bet
    from django.db.models import Sum
    from django.utils import timezone
    
    categoria = request.GET.get('categoria')
    featured_query = Event.objects.exclude(estado='finished').prefetch_related('markets').order_by('fecha_hora')
    if categoria:
        featured_query = featured_query.filter(categoria=categoria)
    featured_events = featured_query[:4]
    
    account = Account.objects.filter(user=request.user, account_type=Account.Tipo.WALLET_USUARIO).first()
    active_bets = Bet.objects.filter(user=request.user, estado=Bet.Estado.PENDING).count()
    wagered_today = Bet.objects.filter(user=request.user, created_at__date=timezone.now().date()).aggregate(t=Sum('monto'))['t'] or 0
    
    return render(request, 'home.html', {
        'page_title': 'Dashboard',
        'featured_events': featured_events,
        'current_categoria': categoria,
        'account': account,
        'active_bets': active_bets,
        'wagered_today': wagered_today,
        'show_sport_bar': True
    })

# Vista de inicio de sesion: valida credenciales con authenticate()
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            return render(request, 'users/login.html', {'error': 'Credenciales inválidas.'})
    return render(request, 'users/login.html')

# Vista de cierre de sesion
def logout_view(request):
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)

# Vista de registro (el formulario usa JS para llamar al API)
def register_view(request):
    return render(request, 'users/register.html')

# Vista del perfil del usuario autenticado
@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'page_title': 'Mi Perfil'})

# Vista de verificacion KYC
@login_required
def kyc_view(request):
    return render(request, 'users/kyc_verify.html', {'page_title': 'Verificación KYC'})

# Vista de limites de deposito
@login_required
def deposit_limits_view(request):
    return render(request, 'users/deposit_limits.html', {'page_title': 'Límites de Depósito'})

# Vista de autoexclusion
@login_required
def self_exclude_view(request):
    return render(request, 'users/self_exclude.html', {'page_title': 'Autoexclusión'})

@login_required
def operator_dashboard_view(request):
    if not request.user.is_staff:
        return redirect('home')
        
    from django.db.models import Sum, Count, F
    from betting.models import Bet, ComboBet, SuspiciousActivity
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Calcular GGR = Total Apostado (won+lost) - Total Pagado (won)
    total_apostado_liquidado_bets = Bet.objects.filter(estado__in=[Bet.Estado.WON, Bet.Estado.LOST]).aggregate(t=Sum('monto'))['t'] or 0
    total_apostado_liquidado_combos = ComboBet.objects.filter(estado__in=[ComboBet.Estado.WON, ComboBet.Estado.LOST]).aggregate(t=Sum('monto'))['t'] or 0
    total_apostado_liquidado = total_apostado_liquidado_bets + total_apostado_liquidado_combos
    
    # Ganancias pagadas (lo que ganaron los usuarios)
    ganancias_pagadas = 0
    bets_won = Bet.objects.filter(estado=Bet.Estado.WON)
    for b in bets_won:
        ganancias_pagadas += b.pago_potencial
        
    combos_won = ComboBet.objects.filter(estado=ComboBet.Estado.WON)
    for c in combos_won:
        ganancias_pagadas += (c.monto * c.cuota_total)
        
    ggr = total_apostado_liquidado - ganancias_pagadas
    
    # Usuarios Activos (registrados en últimas 24h o que apostaron en últimas 24h)
    ayer = timezone.now() - timedelta(days=1)
    usuarios_activos = User.objects.filter(last_login__gte=ayer).count()
    
    # Exposure por evento (cuánto se perdería si todos ganan)
    exposure_total = Bet.objects.filter(estado=Bet.Estado.PENDING).aggregate(t=Sum(F('monto') * F('cuota_al_apostar')))['t'] or 0
    # Add pending combos exposure
    exposure_combos = ComboBet.objects.filter(estado=ComboBet.Estado.PENDING).aggregate(t=Sum(F('monto') * F('cuota_total')))['t'] or 0
    exposure_total += exposure_combos
    
    alertas = SuspiciousActivity.objects.filter(resuelto=False).order_by('-fecha')[:10]
    
    usuarios = User.objects.all().order_by('-date_joined')[:50]

    from events.models import Event
    active_events = Event.objects.exclude(estado__in=[Event.Estado.FINISHED, Event.Estado.CANCELLED]).prefetch_related('markets')

    # Calcular GGR diario para los últimos 7 días
    ggr_labels = []
    ggr_values = []
    for i in range(6, -1, -1):
        dia = timezone.now().date() - timedelta(days=i)
        ggr_labels.append(dia.strftime('%d/%m'))
        
        # Apostado en ese día y ya liquidado
        apostado_dia_bets = Bet.objects.filter(
            estado__in=[Bet.Estado.WON, Bet.Estado.LOST],
            updated_at__date=dia
        ).aggregate(t=Sum('monto'))['t'] or 0
        
        apostado_dia_combos = ComboBet.objects.filter(
            estado__in=[ComboBet.Estado.WON, ComboBet.Estado.LOST],
            updated_at__date=dia
        ).aggregate(t=Sum('monto'))['t'] or 0
        
        apostado_dia = apostado_dia_bets + apostado_dia_combos
        
        # Pagado en ese día
        pagado_dia = 0
        bets_won_dia = Bet.objects.filter(estado=Bet.Estado.WON, updated_at__date=dia)
        for b in bets_won_dia:
            pagado_dia += b.pago_potencial
            
        combos_won_dia = ComboBet.objects.filter(estado=ComboBet.Estado.WON, updated_at__date=dia)
        for c in combos_won_dia:
            pagado_dia += (c.monto * c.cuota_total)
            
        ggr_dia = apostado_dia - pagado_dia
        ggr_values.append(float(ggr_dia))
    
    from wallet.models import Account
    casa_account, _ = Account.objects.get_or_create(account_type=Account.Tipo.CASA)
    saldo_casa = casa_account.balance

    return render(request, 'users/admin_dashboard.html', {
        'page_title': 'Dashboard del Operador',
        'ggr': ggr,
        'saldo_casa': saldo_casa,
        'total_apostado_liquidado': total_apostado_liquidado,
        'ganancias_pagadas': ganancias_pagadas,
        'usuarios_activos': usuarios_activos,
        'exposure_total': exposure_total,
        'alertas': alertas,
        'usuarios': usuarios,
        'active_events': active_events,
        'ggr_labels': ggr_labels,
        'ggr_values': ggr_values,
    })

import csv
from django.http import HttpResponse

@login_required
def export_mincetur_csv(request):
    if not request.user.is_staff:
        return redirect('home')
        
    from betting.models import Bet
    import datetime
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="reporte_mincetur_{datetime.date.today()}.csv"'
    
    # Add BOM for Excel UTF-8 compatibility
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Transaccion', 'DNI Usuario', 'Fecha', 'Evento', 'Mercado', 'Seleccion', 'Monto Apostado (PEN)', 'Cuota', 'Estado', 'Pago (PEN)'])
    
    apuestas = Bet.objects.all().select_related('user', 'event', 'market').order_by('-created_at')
    
    for bet in apuestas:
        writer.writerow([
            bet.id,
            bet.user.dni,
            bet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            f"{bet.event.equipo_local} vs {bet.event.equipo_visitante}",
            bet.market.tipo,
            bet.seleccion,
            f"{bet.monto:.2f}",
            f"{bet.cuota_al_apostar:.2f}",
            bet.estado,
            f"{bet.pago_potencial:.2f}" if bet.estado == Bet.Estado.WON else "0.00"
        ])
        
    return response

@login_required
def add_event_view(request):
    if not request.user.is_staff:
        return redirect('home')
        
    if request.method == 'POST':
        from events.models import Event, Market
        from decimal import Decimal
        from django.utils.dateparse import parse_datetime
        from django.contrib import messages
        
        try:
            categoria = request.POST.get('categoria')
            equipo_local = request.POST.get('equipo_local')
            equipo_visitante = request.POST.get('equipo_visitante')
            fecha_hora = parse_datetime(request.POST.get('fecha_hora'))
            cuota_local = Decimal(request.POST.get('cuota_local'))
            cuota_empate = Decimal(request.POST.get('cuota_empate'))
            cuota_visitante = Decimal(request.POST.get('cuota_visitante'))
            
            # Create Event
            event = Event.objects.create(
                categoria=categoria,
                equipo_local=equipo_local,
                equipo_visitante=equipo_visitante,
                fecha_hora=fecha_hora,
                estado=Event.Estado.SCHEDULED
            )
            
            # Create Default 1X2 Market
            Market.objects.create(
                event=event,
                tipo=Market.Tipo.ONE_X_TWO,
                cuota_local=cuota_local,
                cuota_empate=cuota_empate,
                cuota_visitante=cuota_visitante,
                estado=Market.Estado.OPEN
            )
            
            messages.success(request, 'Evento creado exitosamente.')
            return redirect('operator-dashboard')
            
        except Exception as e:
            messages.error(request, f'Error al crear el evento: {str(e)}')
            
    return render(request, 'users/admin_add_event.html', {'page_title': 'Nuevo Evento'})
