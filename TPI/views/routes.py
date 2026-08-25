"""
Rutas de la aplicación (Capa de Presentación)
Esta capa NO accede directamente a la base de datos
Solo usa la capa de negocio (business)
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from views.forms import RegisterForm, LoginForm, SimulationForm
from business import auth_controller, simulation_controller


def configure_routes(app):
    """Configura todas las rutas de la aplicación"""
    
    @app.route('/')
    def home():
        """Página principal"""
        return render_template('index.html')
    
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Ruta de registro de usuario"""
        # Si ya está autenticado, redirigir al home
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        form = RegisterForm()
        
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            
            # Llamar a la capa de negocio
            result = auth_controller.register_user(username, password)
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('login'))
            else:
                flash(result['message'], 'danger')
        
        return render_template('register.html', form=form)
    
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Ruta de inicio de sesión"""
        # Si ya está autenticado, redirigir al home
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            remember = form.remember_me.data
            
            # Llamar a la capa de negocio
            result = auth_controller.authenticate_user(username, password)
            
            if result['success']:
                login_user(result['user'], remember=remember)
                flash(result['message'], 'success')
                
                # Redirigir a la página solicitada o al home
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash(result['message'], 'danger')
        
        return render_template('login.html', form=form)
    
    
    @app.route('/logout')
    @login_required
    def logout():
        """Ruta de cierre de sesión"""
        logout_user()
        flash('Has cerrado sesión exitosamente', 'info')
        return redirect(url_for('home'))
    
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Panel de control del usuario"""
        # Obtener estadísticas del usuario
        stats = simulation_controller.get_user_statistics(current_user.id)
        
        # Obtener últimas 5 simulaciones
        recent_sessions = simulation_controller.get_user_simulation_history(current_user.id, limit=5)
        
        return render_template('dashboard.html', stats=stats, recent_sessions=recent_sessions)
    
    
    @app.route('/simulator', methods=['GET', 'POST'])
    @login_required
    def simulator():
        """Ruta del simulador BB84"""
        form = SimulationForm()
        
        if form.validate_on_submit():
            # Los parametros viajan por la URL para que la animacion pueda
            # relanzar la simulacion sin volver a pasar por el formulario.
            return redirect(url_for(
                'animation',
                key_length=form.key_length.data,
                noise_rate=form.noise_rate.data,
                eve_strategy=form.eve_strategy.data,
                eve_fraction=form.eve_fraction.data,
                engine=form.engine.data,
            ))

        return render_template('simulator.html', form=form)
    
    
    @app.route('/simulation/<int:session_id>')
    @login_required
    def simulation_result(session_id):
        """Muestra el resultado de una simulación específica"""
        # TODO: Implementar en la siguiente fase
        # Por ahora, redirigir al dashboard
        flash('Visualización de resultados en desarrollo', 'info')
        return redirect(url_for('dashboard'))
    
    
    @app.route('/history')
    @login_required
    def history():
        """Historial completo de simulaciones del usuario"""
        sessions = simulation_controller.get_user_simulation_history(current_user.id, limit=50)
        return render_template('history.html', sessions=sessions)
    
    
    @app.route('/animation')
    @login_required
    def animation():
        """Página de animación del protocolo BB84"""
        return render_template('bb84_animation.html')
    
    
    @app.route('/api/run-simulation', methods=['POST'])
    def run_simulation():
        """API para ejecutar la simulación BB84"""
        try:
            # Verificar si el usuario está autenticado
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': 'No autorizado'}), 403
            
            # silent=True para que un cuerpo vacío o mal formado devuelva 400
            # y no una excepción que termine en 500.
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({
                    'success': False,
                    'message': 'El cuerpo del pedido debe ser un objeto JSON'
                }), 400
            
            try:
                key_length = int(data.get('key_length', 256))
                # Los porcentajes llegan como enteros 0-100 desde la interfaz
                noise_rate = float(data.get('noise_rate', 0)) / 100.0
                eve_fraction = float(data.get('eve_fraction', 100)) / 100.0
            except (TypeError, ValueError):
                return jsonify({
                    'success': False,
                    'message': 'Los parametros numericos son invalidos'
                }), 400

            eve_strategy = data.get('eve_strategy')
            # Retrocompatibilidad con clientes que sigan mandando has_eve
            if eve_strategy is None:
                eve_strategy = (
                    'intercept_resend' if data.get('has_eve') else 'none'
                )

            # Ejecutar simulación (capa de negocio)
            result = simulation_controller.run_bb84_simulation(
                user_id=current_user.id,
                key_length=key_length,
                has_eve=eve_strategy != 'none',
                noise_rate=noise_rate,
                eve_strategy=eve_strategy,
                eve_fraction=eve_fraction,
                engine=data.get('engine', 'analytic'),
            )

            return jsonify(result), 200 if result['success'] else 400
        
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
