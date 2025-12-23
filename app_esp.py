# Importamos las bibliotecas necesarias
import streamlit as st  # Framework para crear la interfaz web
from textblob import TextBlob  # Análisis de sentimientos en inglés
from deep_translator import GoogleTranslator  # Traducción español-inglés
import speech_recognition as sr  # Reconocimiento de voz
from audio_recorder_streamlit import audio_recorder  # Grabador de audio integrado
import tempfile  # Creación de archivos temporales
import os  # Operaciones del sistema operativo

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Analizador de Sentimientos con Voz",  # Título de la pestaña
    page_icon="🎤",  # Ícono de la pestaña
    layout="centered"  # Layout centrado
)

# Título principal de la aplicación
st.title("🎤 Analizador de Sentimientos con Voz")
st.markdown("Escribe **o habla por el micrófono** en español y la IA detectará el tono emocional.")

# Inicializamos el reconocedor de voz
recognizer = sr.Recognizer()

# Variable para almacenar el texto capturado (usando session_state para persistencia)
if 'texto_espanol' not in st.session_state:
    st.session_state.texto_espanol = "¡Estoy muy feliz de aprender inteligencia artificial!"

# Creamos dos pestañas: una para texto y otra para audio
tab1, tab2 = st.tabs(["✍️ Escribir Texto", "🎙️ Hablar por Micrófono"])

# --- PESTAÑA 1: ENTRADA DE TEXTO ---
with tab1:
    st.session_state.texto_espanol = st.text_area(
        "Ingresa tu texto aquí:",  # Etiqueta del área de texto
        value=st.session_state.texto_espanol,  # Valor guardado en sesión
        height=150,  # Altura del área de texto
        key="text_input"  # Clave única para este widget
    )

# --- PESTAÑA 2: ENTRADA DE AUDIO ---
with tab2:
    st.markdown("### 🎙️ Haz clic en el micrófono y habla:")
    st.info("💡 **Instrucciones:** Presiona el botón rojo para grabar, habla claramente en español, y presiona 'Stop' cuando termines.")
    
    # Componente de grabación de audio (captura directamente del micrófono)
    audio_bytes = audio_recorder(
        text="Haz clic para grabar",  # Texto del botón
        recording_color="#e74c3c",  # Color rojo cuando graba
        neutral_color="#3498db",  # Color azul cuando está listo
        icon_name="microphone",  # Ícono de micrófono
        icon_size="3x",  # Tamaño grande del ícono
        pause_threshold=2.0,  # Pausa de 2 segundos para terminar
        sample_rate=16000  # Frecuencia de muestreo óptima para voz
    )
    
    # Si se grabó audio, procesarlo automáticamente
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")  # Reproducir el audio grabado
        
        with st.spinner("🔄 Transcribiendo tu voz..."):  # Indicador de carga
            try:
                # Guardamos el audio en un archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio_bytes)  # Escribimos el contenido del audio
                    tmp_file_path = tmp_file.name  # Guardamos la ruta del archivo
                
                # Procesamos el audio con speech_recognition
                with sr.AudioFile(tmp_file_path) as source:
                    # Ajustamos el reconocedor para ruido ambiente
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)  # Leemos el audio completo
                    
                    # Reconocemos el texto en español usando Google Speech API
                    texto_reconocido = recognizer.recognize_google(
                        audio_data, 
                        language="es-ES"  # Idioma español de España
                    )
                    
                    # Guardamos el texto en session_state
                    st.session_state.texto_espanol = texto_reconocido
                    
                    # Mostramos el resultado con estilo
                    st.success(f"✅ **Texto reconocido:** {texto_reconocido}")
                
                # Eliminamos el archivo temporal para liberar espacio
                os.unlink(tmp_file_path)
                
            except sr.UnknownValueError:  # Error: no se entendió el audio
                st.error("❌ No pude entender lo que dijiste. Por favor, intenta de nuevo hablando más claro.")
            except sr.RequestError as e:  # Error de conexión con el servicio de Google
                st.error(f"❌ Error de conexión con el servicio de reconocimiento: {e}")
            except Exception as e:  # Cualquier otro error inesperado
                st.error(f"❌ Error al procesar el audio: {e}")
    
    st.markdown("---")
    st.markdown("**💡 Consejos para mejor reconocimiento:**")
    st.markdown("""
    - Habla claramente y a un ritmo normal
    - Evita ruidos de fondo
    - Mantén el micrófono cerca
    - Espera a que aparezca el audio antes de analizar
    """)

# --- BOTÓN DE ANÁLISIS ---
st.markdown("---")
if st.button("🔍 Analizar Sentimiento", type="primary", use_container_width=True):
    # Verificamos que haya texto para analizar
    if st.session_state.texto_espanol and st.session_state.texto_espanol.strip():
        try:
            # --- PASO 1: TRADUCCIÓN ESPAÑOL → INGLÉS ---
            # TextBlob funciona mejor con inglés, por eso traducimos
            traductor = GoogleTranslator(source='es', target='en')
            texto_ingles = traductor.translate(st.session_state.texto_espanol)
            
            # Mostramos la traducción interna (opcional, para transparencia)
            st.caption(f"⚙️ Traducción interna: *'{texto_ingles}'*")

            # --- PASO 2: ANÁLISIS DE SENTIMIENTOS ---
            blob = TextBlob(texto_ingles)  # Creamos objeto TextBlob
            polaridad = blob.sentiment.polarity  # Valor entre -1 (negativo) y 1 (positivo)
            subjetividad = blob.sentiment.subjectivity  # Valor entre 0 (objetivo) y 1 (subjetivo)
            
            # --- PASO 3: VISUALIZACIÓN DE RESULTADOS ---
            st.write("---")
            st.subheader("📊 Resultados del Análisis:")
            
            # Mostramos el texto analizado
            st.info(f"**📝 Texto analizado:** {st.session_state.texto_espanol}")
            
            # Creamos tres columnas para mostrar métricas
            col1, col2, col3 = st.columns(3)
            
            # Clasificamos el sentimiento según la polaridad
            with col1:
                if polaridad > 0.1:  # Sentimiento positivo
                    st.metric("Sentimiento", "😊 Positivo", f"{polaridad:.2f}")
                elif polaridad < -0.1:  # Sentimiento negativo
                    st.metric("Sentimiento", "😠 Negativo", f"{polaridad:.2f}")
                else:  # Sentimiento neutral
                    st.metric("Sentimiento", "😐 Neutral", f"{polaridad:.2f}")
            
            # Mostramos la polaridad en escala
            with col2:
                st.metric("Polaridad", f"{polaridad:.2f}", "(-1 a +1)")
            
            # Mostramos la subjetividad en escala
            with col3:
                st.metric("Subjetividad", f"{subjetividad:.2f}", f"{(subjetividad * 100):.0f}%")
            
            # Explicación de los valores
            st.markdown("---")
            st.markdown("### 📖 Interpretación:")
            st.markdown(f"""
            - **Polaridad**: Mide si el texto es positivo, negativo o neutral.
              - Tu texto tiene un score de **{polaridad:.2f}** (donde -1 es muy negativo y +1 es muy positivo)
            
            - **Subjetividad**: Mide si el texto es opinión o hecho objetivo.
              - Tu texto es **{(subjetividad * 100):.0f}% subjetivo** (opinión personal vs. hecho objetivo)
            """)
            
            # Barra de progreso visual para polaridad
            st.markdown("#### Escala de Polaridad:")
            # Normalizamos la polaridad de -1,1 a 0,1 para la barra de progreso
            progreso_polaridad = (polaridad + 1) / 2
            st.progress(progreso_polaridad)
            
            # Interpretación adicional según el resultado
            st.markdown("---")
            if polaridad > 0.5:
                st.success("🎉 ¡Tu mensaje transmite mucha energía positiva!")
            elif polaridad > 0.1:
                st.success("😊 Tu mensaje tiene un tono positivo.")
            elif polaridad < -0.5:
                st.error("😢 Tu mensaje refleja emociones negativas fuertes.")
            elif polaridad < -0.1:
                st.warning("😔 Tu mensaje tiene un tono algo negativo.")
            else:
                st.info("😐 Tu mensaje es neutral, sin emociones marcadas.")
            
        except Exception as e:  # Capturamos cualquier error
            st.error(f"❌ Hubo un error en el análisis: {e}")
            
    else:  # Si no hay texto
        st.warning("⚠️ Por favor escribe o graba un mensaje para analizar.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    💡 Desarrollado con Streamlit | 🧠 Análisis con TextBlob | 🌐 Traducción con GoogleTranslator | 🎤 Grabación con audio-recorder-streamlit
</div>
""", unsafe_allow_html=True)