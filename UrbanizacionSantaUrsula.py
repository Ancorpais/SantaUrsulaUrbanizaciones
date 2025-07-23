# CONFIGURACION

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import math
import json
from datetime import datetime
import email.message
import smtplib
import logging

# Cargar datos config
dataset = "\\\\172.33.154.245//datos//ArcGISPro//urbanizaciones_santa_ursula//Script//Python//config.json"
with open(dataset, "r", encoding="utf-8") as file:
    config = json.load(file)
    capa_urbanizacion = config.get("capa_urbanizacion")
    portal = config.get("portal")
    user = config.get("user")
    password = config.get("password")
    fecha_ult_actualizacion = config.get("fecha_ult_actualizacion")

# Conectar Portal
gis = GIS(portal, user, password)
reporte_feature_update = []

# Capa base donde se encuentra el feature original
urbanizaciones_layer = FeatureLayer(capa_urbanizacion, gis)


# Calcular el valor del campo sup_urb
def calculate_supUrb(query_result):
    total_supUrb = 0

    for feature in query_result.features:
        urb = feature.attributes.get('urbaniz')
        sup_tramo = feature.attributes.get('sup_tramo')

        if urb is not None and urb != "":
            total_supUrb += sup_tramo or 0

    features_to_update = []

    for feature in query_result.features:
        attrs = feature.attributes
        attrs["sup_tramo"] = total_supUrb
        features_to_update.append({"attributes": attrs})
        reporte_feature_update.append(attrs["objectid"])

    update_result = urbanizaciones_layer.edit_features(updates=features_to_update)

    # Verificar resultado
    if 'updateResults' in update_result:
        print("Actualización completada. Entidades modificadas:", len(update_result['updateResults']))
    else:
        print("Error al actualizar:", update_result)


# Calcular el valor del campo longitud_urbaniz
def calculate_longitudUrbaniz(query_result):
    total_longitudUrbaniz = 0

    for feature in query_result.features:
        urb = feature.attributes.get('urbaniz')
        longitud_tramo = feature.attributes.get('longitud_tramo')

        if urb is not None and urb != "":
            total_longitudUrbaniz += longitud_tramo or 0

    features_to_update = []

    for feature in query_result.features:
        attrs = feature.attributes
        attrs["longitud_urbaniz"] = total_longitudUrbaniz
        features_to_update.append({"attributes": attrs})
        reporte_feature_update.append(attrs["objectid"])

    update_result = urbanizaciones_layer.edit_features(updates=features_to_update)

    # Verificar resultado
    if 'updateResults' in update_result:
        print("Actualización completada. Entidades modificadas:", len(update_result['updateResults']))
    else:
        print("Error al actualizar:", update_result)


# Obtener entidades a actualizar
def entidades_Actualizar():
    expresion = f"last_edited_date > DATE '{fecha_ult_actualizacion}'"
    urbanizaciones_actualizar = urbanizaciones_layer.query(where=expresion,
                                                           out_fields="objectid,urbaniz,sup_tramo,longitud_urbaniz,longitud_tramo",
                                                           return_geometry=False)

    urbaniz_actualizadas = []

    for urb in urbanizaciones_actualizar:

        if urb.attributes['urbaniz'] not in urbaniz_actualizadas:
            urbaniz_actualizadas.append(urb.attributes['urbaniz'])
            expresion = "urbaniz = " + str(urb.attributes['urbaniz'])
            query_result = urbanizaciones_layer.query(where=expresion,
                                                      out_fields="objectid,urbaniz,sup_tramo,longitud_urbaniz,longitud_tramo",
                                                      return_geometry=False)

            calculate_supUrb(query_result)
            calculate_longitudUrbaniz(query_result)


# Actualizar fecha de ultima actualizacion
def actualizar_fechaModif():
    try:
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Actualizar el archivo JSON
        with open("\\\\172.33.154.245//datos//ArcGISPro//urbanizaciones_santa_ursula//Script//Python//config.json", 'r') as archivo:
            data = json.load(archivo)
            data['fecha_ult_actualizacion'] = fecha_actual

        with open('config.json', 'w') as archivo:
            json.dump(data, archivo, indent=4)

        logging.shutdown()
        print("Proceso finalizado.")

    except Exception as e:
        logging.error(' Ha ocurrido un error al modificar la fecha de actualizacon en el json: ' + str(e))
        print('Ha ocurrido un error al modificar la fecha de actualizacon en el json: ' + str(e))


# Enviar correo
def send_email_smtp(msg, smtp_server_url, smtp_server_port, username, password, recipients):
    try:
        # Instantiate our server, configure the necessary security
        server = smtplib.SMTP(smtp_server_url, smtp_server_port)
        server.ehlo()
        server.starttls()
        server.login(username, password)
    except Exception as e:
        print("Error configurando el servidor SMTP. No se pudo enviar.")
        raise e

    # For each recipient, construct the message and attempt to send
    did_succeed = True
    for recipient in recipients:
        try:
            server.sendmail(msg["From"], [recipient], msg.as_string())
            print(f"Correo enviado correctamente a {recipient}")
        except Exception as e:
            print(f"Error al enviar el correo a {recipient}")
            print(e)
            did_succeed = False

    # Cleanup and return
    server.quit()
    return did_succeed


def enviarCorreo(bdyErr):
    max_inactive_days = 180
    recipients = ['apaitos@gesplan.es', 'jpermen@gesplan.es']
    # Set up server and credential variables
    smtp_server_url = "smtp.gmail.com"
    smtp_server_port = 587
    username = "oficinadeldato@gesplan.es"
    password = 'nyxw jiou xkbo fuyo'
    msg = email.message.EmailMessage()
    msg["From"] = "oficinadeldato@gesplan.es"
    msg['Subject'] = 'Reporte de actualizacion de capa Urbanización de Santa Ursula'
    if bdyErr:
        body = "<html>" + bdyErr + "</html>"
    else:
        body = "<html>Se ha ejecutado correctamente el script de calculo de campo sup_urb del proyecto de Santa Ursula.</html>"
    msg.set_content(body, subtype='html')
    send_email_smtp(msg, smtp_server_url, smtp_server_port, username, password, recipients)


if __name__ == "__main__":

    entidades_Actualizar()
    actualizar_fechaModif()

    # Enviar correo
    expediente_modif = ""
    for exp in reporte_feature_update:
        expediente_modif += str(exp) + "; "

    enviarCorreo(
        "<html>Se ha ejecutado correctamente el script de calculo de campo sup_urb del proyecto de Santa Ursula.<br>"
        "Expedientes actualizados: " + expediente_modif + "</html>")
