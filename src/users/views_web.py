from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from users.models import User


# Vista del Dashboard Principal
@login_required
def home_view(request):
    from events.models import Event
    featured_events = Event.objects.exclude(estado='finished').order_by('fecha_hora')[:4]
    return render(request, 'home.html', {
        'page_title': 'Dashboard',
        'featured_events': featured_events
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
    from betting.models import Bet, SuspiciousActivity
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Calcular GGR = Total Apostado (won+lost) - Total Pagado (won)
    total_apostado_liquidado = Bet.objects.filter(estado__in=[Bet.Estado.WON, Bet.Estado.LOST]).aggregate(t=Sum('monto'))['t'] or 0
    
    # Ganancias pagadas (lo que ganaron los usuarios)
    ganancias_pagadas = 0
    bets_won = Bet.objects.filter(estado=Bet.Estado.WON)
    for b in bets_won:
        ganancias_pagadas += b.pago_potencial
        
    ggr = total_apostado_liquidado - ganancias_pagadas
    
    # Usuarios Activos (registrados en últimas 24h o que apostaron en últimas 24h)
    ayer = timezone.now() - timedelta(days=1)
    usuarios_activos = User.objects.filter(last_login__gte=ayer).count()
    
    # Exposure por evento (cuánto se perdería si todos ganan)
    exposure_total = Bet.objects.filter(estado=Bet.Estado.PENDING).aggregate(t=Sum(F('monto') * F('cuota_al_apostar')))['t'] or 0
    
    alertas = SuspiciousActivity.objects.filter(resuelto=False).order_by('-fecha')[:10]
    
    usuarios = User.objects.all().order_by('-date_joined')[:50]

    
    return render(request, 'users/admin_dashboard.html', {
        'page_title': 'Dashboard del Operador',
        'ggr': ggr,
        'total_apostado_liquidado': total_apostado_liquidado,
        'ganancias_pagadas': ganancias_pagadas,
        'usuarios_activos': usuarios_activos,
        'exposure_total': exposure_total,
        'alertas': alertas,
        'usuarios': usuarios,
    })

import csv
from django.http import HttpResponse

@login_required
def export_mincetur_csv(request):
    if not request.user.is_staff:
        return redirect('home')
        
    from betting.models import Bet
    import datetime
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_mincetur_{datetime.date.today()}.csv"'
    
    writer = csv.writer(response)
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
            f"{bet.cuota_actual:.2f}",
            bet.estado,
            f"{bet.pago_potencial:.2f}" if bet.estado == Bet.Estado.WON else "0.00"
        ])
        
    return response

