package com.optem.ui;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

import com.optem.auth.AuthManager;

import javafx.animation.AnimationTimer;
import javafx.animation.FadeTransition;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.geometry.Side;
import javafx.scene.Scene;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ContextMenu;
import javafx.scene.control.Label;
import javafx.scene.control.MenuItem;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Pane;
import javafx.scene.layout.Priority;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.stage.Stage;
import javafx.util.Duration;

public class LoginView {

    private boolean isPasswordVisible = false;
    private Random random = new Random();
    private List<InteractiveBubble> activeBubbles = new ArrayList<>();
    private static final double LEFT_PANEL_WIDTH = 550;

    public void show(Stage stage) {
        HBox mainLayout = new HBox();
        mainLayout.setStyle("-fx-background-color: white;");

        // PANEL IZQUIERDO 
        Pane leftPane = new Pane(); 
        leftPane.setMinWidth(LEFT_PANEL_WIDTH);
        leftPane.setMaxWidth(LEFT_PANEL_WIDTH);
        leftPane.setStyle("-fx-background-color: #3D5A4D;");

        // Burbujas de fondo
        for (int i = 0; i < 30; i++) { createNewBubble(leftPane); }

        AnimationTimer physicsTimer = new AnimationTimer() {
            @Override
            public void handle(long now) {
                for (InteractiveBubble b : activeBubbles) { b.update(); }
            }
        };
        physicsTimer.start();

        // Bloque de información FIJO
        VBox infoBox = new VBox(45);
        infoBox.setAlignment(Pos.CENTER);
        infoBox.setPrefWidth(LEFT_PANEL_WIDTH);
        infoBox.setMouseTransparent(true); 
        infoBox.setLayoutY(150); 

        HBox logos = new HBox(30);
        logos.setAlignment(Pos.CENTER);
        try {
            InputStream stUaem = getClass().getResourceAsStream("/images/uaem_escudo.png");
            InputStream stOptem = getClass().getResourceAsStream("/images/logo_optem_white.png");
            if (stUaem != null) {
                ImageView ivU = new ImageView(new Image(stUaem));
                ivU.setFitWidth(110); ivU.setPreserveRatio(true);
                logos.getChildren().add(ivU);
            }
            if (stOptem != null) {
                ImageView ivO = new ImageView(new Image(stOptem));
                ivO.setFitWidth(190); 
                ivO.setPreserveRatio(true);
                logos.getChildren().add(ivO);
            }
        } catch(Exception e) {}

        Label lblOptem = new Label("OPTEM");
        lblOptem.setStyle("-fx-font-size: 75; -fx-font-weight: bold; -fx-text-fill: #E9EDC9; -fx-letter-spacing: 12;");

        VBox features = new VBox(22);
        features.setPadding(new Insets(0, 0, 0, 120)); 
        features.setAlignment(Pos.CENTER_LEFT);
        features.getChildren().addAll(
            createFeatureItem("📅  Agenda y horario académico"),
            createFeatureItem("⏱  Técnica Pomodoro"),
            createFeatureItem("⭐  Sistema de XP y logros"),
            createFeatureItem("🔔  Alertas de entregas")
        );

        infoBox.getChildren().addAll(logos, lblOptem, features);
        leftPane.getChildren().add(infoBox);

        // PANEL DERECHO 
        VBox rightPane = new VBox(20);
        HBox.setHgrow(rightPane, Priority.ALWAYS);
        rightPane.setAlignment(Pos.CENTER);
        rightPane.setPadding(new Insets(50));

        VBox form = new VBox(15);
        form.setMaxWidth(500); 
        form.setAlignment(Pos.CENTER_LEFT);

        Label lblLogin = new Label("Iniciar sesión");
        lblLogin.setStyle("-fx-font-size: 38; -fx-font-weight: bold; -fx-text-fill: #1B263B;");
        
        String roundStyle = "-fx-background-radius: 30; -fx-border-radius: 30; -fx-padding: 12 20; -fx-border-color: #ddd; -fx-background-color: white;";

        // CAMPO CORREO
        TextField txtUser = new TextField();
        txtUser.setPromptText("usuario@alumno.uaemex.mx");
        txtUser.setStyle(roundStyle);
        txtUser.setMaxWidth(Double.MAX_VALUE);

        // ContextMenu
        ContextMenu suggestions = new ContextMenu();
        suggestions.setStyle("-fx-background-radius: 15; -fx-border-radius: 15; -fx-border-color: #B38E5D;");
        MenuItem itemAlumno = new MenuItem("@alumno.uaemex.mx");
        MenuItem itemDocente = new MenuItem("@uaemex.mx");
        suggestions.getItems().addAll(itemAlumno, itemDocente);

        txtUser.textProperty().addListener((obs, old, nVal) -> {
            if (nVal.contains("@") && !nVal.endsWith(".mx")) {
                suggestions.show(txtUser, Side.BOTTOM, 0, 0);
            } else { suggestions.hide(); }
        });

        itemAlumno.setOnAction(e -> { txtUser.setText(txtUser.getText().split("@")[0] + "@alumno.uaemex.mx"); txtUser.requestFocus(); txtUser.selectEnd(); });
        itemDocente.setOnAction(e -> { txtUser.setText(txtUser.getText().split("@")[0] + "@uaemex.mx"); txtUser.requestFocus(); txtUser.selectEnd(); });

        //CAMPO CONTRASEÑA 
        PasswordField txtPass = new PasswordField();
        TextField txtPassVis = new TextField();
        txtPassVis.setManaged(false); txtPassVis.setVisible(false);
        txtPass.setPromptText("Contraseña");
        txtPassVis.setPromptText("Contraseña");
        
        String passStyle = "-fx-background-radius: 30; -fx-border-radius: 30; -fx-padding: 12 50 12 20; -fx-border-color: #ddd; -fx-background-color: white;";
        txtPass.setStyle(passStyle); 
        txtPassVis.setStyle(passStyle);
        
        txtPass.setMaxWidth(Double.MAX_VALUE);
        txtPassVis.setMaxWidth(Double.MAX_VALUE);
        StackPane.setMargin(txtPass, new Insets(0, 0, 0, 0));
        StackPane.setMargin(txtPassVis, new Insets(0, 0, 0, 0));

        Button btnEye = new Button("👁");
        btnEye.setStyle("-fx-background-color: transparent; -fx-cursor: hand; -fx-text-fill: #888; -fx-font-size: 16;");
        btnEye.setMaxHeight(Double.MAX_VALUE); 

        btnEye.setOnAction(e -> {
            isPasswordVisible = !isPasswordVisible;
            if (isPasswordVisible) {
                txtPassVis.setText(txtPass.getText());
                txtPass.setManaged(false); txtPass.setVisible(false);
                txtPassVis.setManaged(true); txtPassVis.setVisible(true);
            } else {
                txtPass.setText(txtPassVis.getText());
                txtPassVis.setManaged(false); txtPassVis.setVisible(false);
                txtPass.setManaged(true); txtPass.setVisible(true);
            }
        });

        StackPane passStack = new StackPane(txtPass, txtPassVis, btnEye);
        passStack.setMaxWidth(Double.MAX_VALUE);
        passStack.setAlignment(Pos.CENTER_RIGHT); 
        StackPane.setMargin(btnEye, new Insets(0, 15, 0, 0)); 

        // TARJETAS DE SELECCIÓN
        HBox cards = new HBox(20);
        cards.setAlignment(Pos.CENTER);
        VBox cardEst = createMiniCard("Estudiante", "🎓", stage, txtUser, txtPass, txtPassVis);
        VBox cardAdm = createMiniCard("Administrativo", "🏛", stage, txtUser, txtPass, txtPassVis);
        cards.getChildren().addAll(cardEst, cardAdm);

        form.getChildren().addAll(lblLogin, new Label("  Correo"), txtUser, new Label("  Contraseña"), passStack, new Label("\n  Tipo de cuenta"), cards);
        rightPane.getChildren().add(form);

        mainLayout.getChildren().addAll(leftPane, rightPane);
        Scene scene = new Scene(mainLayout);
        
        // Estilos CSS Oro UAEMéx
        scene.getStylesheets().add("data:text/css," + 
            ".context-menu { -fx-background-color: white; -fx-background-radius: 10; -fx-border-color: #B38E5D; }" +
            ".menu-item:focused { -fx-background-color: #B38E5D; }" + 
            ".menu-item:focused .label { -fx-text-fill: white; }");

        stage.setScene(scene);
        stage.setMaximized(true);
        stage.show();
    }

    private void createNewBubble(Pane pane) {
        InteractiveBubble b = new InteractiveBubble(
            15 + random.nextDouble() * 45, 
            Color.web("#FFFFFF", 0.12), 
            pane
        );
        activeBubbles.add(b);
        b.shape.setOnMouseClicked(e -> explodeBubble(pane, b));
    }

    private void explodeBubble(Pane pane, InteractiveBubble parent) {
        activeBubbles.remove(parent);
        pane.getChildren().remove(parent.shape);
        double px = parent.shape.getLayoutX();
        double py = parent.shape.getLayoutY();
        for (int i = 0; i < 10; i++) {
            InteractiveBubble p = new InteractiveBubble(6, Color.web("#FFFFFF", 0.18), pane);
            p.shape.setLayoutX(px); p.shape.setLayoutY(py);
            p.vx = (random.nextDouble() - 0.5) * 22; 
            p.vy = (random.nextDouble() - 0.5) * 22;
            activeBubbles.add(p);
            FadeTransition ft = new FadeTransition(Duration.seconds(3.5), p.shape);
            ft.setToValue(0);
            ft.setOnFinished(e -> {
                activeBubbles.remove(p);
                pane.getChildren().remove(p.shape);
                if (activeBubbles.size() < 30) createNewBubble(pane);
            });
            ft.play();
        }
    }

    class InteractiveBubble {
        Circle shape;
        double vx, vy;
        double radius;

        InteractiveBubble(double r, Color c, Pane pane) {
            this.radius = r;
            shape = new Circle(r, c);
            shape.setStroke(Color.web("#FFFFFF", 0.2));
            shape.setLayoutX(random.nextDouble() * LEFT_PANEL_WIDTH);
            shape.setLayoutY(random.nextDouble() * 800);
            vx = (random.nextDouble() - 0.5) * 1.3; 
            vy = (random.nextDouble() - 0.5) * 1.3;
            pane.getChildren().add(0, shape); 
        }

        void update() {
            shape.setLayoutX(shape.getLayoutX() + vx);
            shape.setLayoutY(shape.getLayoutY() + vy);
            if (shape.getLayoutX() <= radius || shape.getLayoutX() >= LEFT_PANEL_WIDTH - radius) { vx *= -1; }
            if (shape.getLayoutY() <= radius || shape.getLayoutY() >= 1000) { vy *= -1; }
        }
    }

    private VBox createMiniCard(String type, String icon, Stage s, TextField u, PasswordField p, TextField v) {
        VBox card = new VBox(10);
        card.setPrefSize(200, 140);
        card.setAlignment(Pos.CENTER);
        card.setStyle("-fx-background-color: #fcfcfc; -fx-background-radius: 25; -fx-border-color: #eee; -fx-border-radius: 25; -fx-cursor: hand;");

        Label lblIcon = new Label(icon); lblIcon.setStyle("-fx-font-size: 28;");
        Label lblType = new Label(type); lblType.setStyle("-fx-font-weight: bold; -fx-font-size: 15;");
        
        Button btnEntrar = new Button("Entrar");
        btnEntrar.setDisable(true);
        btnEntrar.setStyle("-fx-background-color: #3D5A4D; -fx-text-fill: white; -fx-background-radius: 20;");

        card.setOnMouseClicked(e -> {
            card.getParent().getChildrenUnmodifiable().forEach(node -> node.setStyle("-fx-background-color: #fcfcfc; -fx-background-radius: 25; -fx-border-color: #eee; -fx-border-radius: 25;"));
            card.setStyle("-fx-background-color: #E9EDC9; -fx-background-radius: 25; -fx-border-color: #3D5A4D; -fx-border-radius: 25; -fx-border-width: 2;");
            btnEntrar.setDisable(false);
        });

        btnEntrar.setOnAction(e -> {
            String pass = isPasswordVisible ? v.getText() : p.getText();
            AuthManager auth = new AuthManager();
            Map<String, String> res = auth.iniciarSesion(u.getText(), pass);
            if(res.get("status").equals("success")) {
                s.close();
                new DashboardView().show(new Stage(), res.get("nombre"), res.get("file_key"));
            } else {
                Alert alert = new Alert(Alert.AlertType.ERROR);
                alert.setContentText(res.get("message"));
                alert.showAndWait();
            }
        });

        card.getChildren().addAll(lblIcon, lblType, btnEntrar);
        return card;
    }

    private HBox createFeatureItem(String text) {
        Label l = new Label(text);
        l.setStyle("-fx-text-fill: white; -fx-font-size: 17; -fx-font-family: 'Segoe UI';");
        return new HBox(l);
    }
}