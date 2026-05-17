package com.optem.models;

import java.time.LocalTime;

public class Actividad {
    private String nombre;
    private String tipo; // "Estudio", "Tarea", "Examen", "Proyecto", "Cultural", "Personal", "Reunión", "Deporte"
    private LocalTime horaVencimiento;
    private boolean hecho;

    public Actividad(String nombre, String tipo, LocalTime horaVencimiento, boolean hecho) {
        this.nombre = nombre;
        this.tipo = tipo;
        this.horaVencimiento = horaVencimiento;
        this.hecho = hecho;
    }

    // Getters y Setters
    public String getNombre() { return nombre; }
    public void setNombre(String nombre) { this.nombre = nombre; }

    public String getTipo() { return tipo; }
    public void setTipo(String tipo) { this.tipo = tipo; }

    public LocalTime getHoraVencimiento() { return horaVencimiento; }
    public void setHoraVencimiento(LocalTime horaVencimiento) { this.horaVencimiento = horaVencimiento; }

    public boolean isHecho() { return hecho; }
    public void setHecho(boolean hecho) { this.hecho = hecho; }
}