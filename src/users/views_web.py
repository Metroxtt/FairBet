from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Vista del Dashboard Principal
@login_required
def home_view(request):
    return render(request, 'home.html', {'page_title': 'Dashboard'})

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
        
    from django.db.models import Sum
    from betting.models import Bet
    
    # Calcular GGR = Total Apostado (won+lost) - Total Pagado (won)
    total_apostado_liquidado = Bet.objects.filter(estado__in=[Bet.Estado.WON, Bet.Estado.LOST]).aggregate(t=Sum('monto'))['t'] or 0
    
    # Ganancias pagadas (lo que ganaron los usuarios)
    ganancias_pagadas = 0
    bets_won = Bet.objects.filter(estado=Bet.Estado.WON)
    for b in bets_won:
        ganancias_pagadas += b.pago_potencial
        
    ggr = total_apostado_liquidado - ganancias_pagadas
    
    return render(request, 'users/admin_dashboard.html', {
        'page_title': 'Dashboard del Operador',
        'ggr': ggr,
        'total_apostado_liquidado': total_apostado_liquidado,
        'ganancias_pagadas': ganancias_pagadas
    })
