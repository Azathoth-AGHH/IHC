package com.optem;

import com.optem.ui.LoginView;
import com.optem.ui.SplashScreen;

import javafx.application.Application;
import javafx.stage.Stage;

public class MainApp extends Application {
    @Override
    public void start(Stage primaryStage) {
        SplashScreen splash = new SplashScreen();
        splash.show(primaryStage, () -> {
            LoginView login = new LoginView();
            login.show(new Stage()); 
        });
    }

    public static void main(String[] args) {
        launch(args);
    }
}