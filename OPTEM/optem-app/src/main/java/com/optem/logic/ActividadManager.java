package com.optem.logic;

import java.time.LocalTime;
import java.util.Comparator;

import com.optem.models.Actividad;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;

public class ActividadManager {
    
    private static ActividadManager instance;
    private final ObservableList<Actividad> listaActividades;

    private ActividadManager() {
        listaActividades = FXCollections.observableArrayList();
        cargarDatosSimulados();
    }

    public static ActividadManager getInstance() {
        if (instance == null) {
            instance = new ActividadManager();
        }
        return instance;
    }

    private void cargarDatosSimulados() {
        listaActividades.add(new Actividad("Estudio grupal: Examen Física II", "Estudio", LocalTime.of(7, 0), true));
        listaActividades.add(new Actividad("Clase: Base de Datos Avanzadas", "Estudio", LocalTime.of(8, 30), true));
        listaActividades.add(new Actividad("Taller: Música y bienestar estudiantil", "Cultural", LocalTime.of(12, 0), false));
        listaActividades.add(new Actividad("Descanso programado", "Personal", LocalTime.of(15, 0), false));
        listaActividades.add(new Actividad("Clase: Sistemas Operativos", "Estudio", LocalTime.of(16, 30), false));
        listaActividades.add(new Actividad("Junta: Semana de bienvenida", "Reunión", LocalTime.of(18, 0), true));
        listaActividades.add(new Actividad("Carrera: 5K Campus UAEMéx", "Deporte", LocalTime.of(19, 30), false));
        listaActividades.add(new Actividad("Taller: Diseño UX/UI para apps", "Cultural", LocalTime.of(21, 0), false));
    }

    // Retorna las actividades ordenadas por hora
    public ObservableList<Actividad> getActividadesDelDia() {
        FXCollections.sort(listaActividades, Comparator.comparing(Actividad::getHoraVencimiento));
        return listaActividades;
    }

    // Calculo del porcentaje real completado para rellenar la barra de progreso
    public double calcularProgresoDelDia() {
        if (listaActividades.isEmpty()) return 0.0;
        long completadas = listaActividades.stream().filter(Actividad::isHecho).count();
        return (double) completadas / listaActividades.size();
    }
}