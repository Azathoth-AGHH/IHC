package com.optem.ui;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.prefs.Preferences;

import com.optem.logic.ActividadManager;
import com.optem.models.Actividad;

import javafx.animation.Animation;
import javafx.animation.FadeTransition;
import javafx.animation.Interpolator;
import javafx.animation.KeyFrame;
import javafx.animation.KeyValue;
import javafx.animation.RotateTransition;
import javafx.animation.Timeline;
import javafx.application.Platform;
import javafx.beans.property.SimpleObjectProperty;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.TableCell;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableRow;
import javafx.scene.control.TableView;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.effect.DropShadow;
import javafx.scene.effect.InnerShadow;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.input.ClipboardContent;
import javafx.scene.input.Dragboard;
import javafx.scene.input.TransferMode;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.GridPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Pane;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.scene.shape.Polygon;
import javafx.scene.shape.Rectangle;
import javafx.stage.Stage;
import javafx.util.Duration;

public class DashboardView {

    private boolean isSidebarExpanded = true;
    private static final double EXPANDED_WIDTH = 260;
    private static final double COLLAPSED_WIDTH = 75;
    
    private final Preferences prefs = Preferences.userNodeForPackage(DashboardView.class);
    private Label lblCurrentBook;
    private Button btnResumeBook;
    private Timeline mediaTrackerTimeline;
    private ProgressBar xpBar; 

    // Control de posición y estado del Chatbot Flotante y Arrastrable
    private boolean isChatOpen = false;
    private VBox chatWindow;
    private Button btnChatToggle;
    private TextArea txtChatHistory; 
    private double dragStartX = 0;
    private double dragStartY = 0;

    public void show(Stage stage, String nombreUsuario, String fileKey) {
        StackPane mainRoot = new StackPane();
        
        BorderPane root = new BorderPane();
        root.setStyle("-fx-background-color: #f8f9fa;");

        // 1. SIDEBAR RETRÁCTIL
        VBox sidebar = new VBox(10);
        sidebar.setPrefWidth(EXPANDED_WIDTH);
        sidebar.setMinWidth(COLLAPSED_WIDTH);
        sidebar.setMaxWidth(EXPANDED_WIDTH);
        sidebar.setPadding(new Insets(15, 20, 15, 20));
        sidebar.setStyle("-fx-background-color: #ffffff; -fx-border-color: #eee; -fx-border-width: 0 1 0 0;");

        Button btnToggle = new Button("≡");
        btnToggle.setStyle("-fx-background-color: transparent; -fx-font-size: 26; -fx-font-weight: bold; -fx-cursor: hand; -fx-text-fill: #555; -fx-padding: 0 0 10 5;");
        btnToggle.setAlignment(Pos.CENTER_LEFT);

        VBox userBox = new VBox(10);
        userBox.setAlignment(Pos.CENTER);
        userBox.setPadding(new Insets(10, 0, 20, 0));
        Circle userPic = new Circle(35, Color.web("#3D5A4D"));
        Label lblName = new Label(nombreUsuario);
        lblName.setStyle("-fx-font-weight: bold; -fx-font-size: 15;");
        userBox.getChildren().addAll(userPic, lblName);

        VBox menuButtonsBox = new VBox(12);
        Button btnInicio = createMenuButton("🏠", "Inicio", true);
        Button btnAgenda = createMenuButton("📅", "Mi Agenda", false);
        Button btnActividades = createMenuButton("🎯", "Actividades", false);
        Button btnPomodoro = createMenuButton("⏱", "Pomodoro", false);
        Button btnLogros = createMenuButton("🏆", "Logros", false);
        Button btnReinscripcion = createMenuButton("📝", "Reinscripción", false);
        Button btnAjustes = createMenuButton("⚙", "Ajustes", false);

        menuButtonsBox.getChildren().addAll(btnInicio, btnAgenda, btnActividades, btnPomodoro, btnLogros, btnReinscripcion, btnAjustes);
        sidebar.getChildren().addAll(btnToggle, userBox, menuButtonsBox);

        btnToggle.setOnAction(e -> {
            isSidebarExpanded = !isSidebarExpanded;
            double targetWidth = isSidebarExpanded ? EXPANDED_WIDTH : COLLAPSED_WIDTH;
            Timeline timeline = new Timeline(
                new KeyFrame(Duration.ZERO, new KeyValue(sidebar.prefWidthProperty(), sidebar.getWidth())),
                new KeyFrame(Duration.millis(200), new KeyValue(sidebar.prefWidthProperty(), targetWidth))
            );
            timeline.setOnFinished(evt -> {
                if (!isSidebarExpanded) {
                    sidebar.setPadding(new Insets(15, 10, 15, 10));
                    userBox.getChildren().remove(lblName);
                    userPic.setRadius(22);
                    toggleButtonTexts(false, btnInicio, btnAgenda, btnActividades, btnPomodoro, btnLogros, btnReinscripcion, btnAjustes);
                } else {
                    sidebar.setPadding(new Insets(15, 20, 15, 20));
                    if (!userBox.getChildren().contains(lblName)) userBox.getChildren().add(lblName);
                    userPic.setRadius(35);
                    toggleButtonTexts(true, btnInicio, btnAgenda, btnActividades, btnPomodoro, btnLogros, btnReinscripcion, btnAjustes);
                }
            });
            timeline.play();
        });

        // 2. ÁREA DE CONTENIDO PRINCIPAL
        VBox mainContent = new VBox(25);
        mainContent.setPadding(new Insets(30, 35, 30, 35));
        
        ScrollPane scroll = new ScrollPane(mainContent);
        scroll.setFitToWidth(true);

        //BANNER CON HEXÁGONOS
        StackPane bannerContainer = new StackPane();
        bannerContainer.setPrefHeight(170);
        bannerContainer.setMinHeight(170);

        Pane bannerBackground = new Pane();
        bannerBackground.setStyle("-fx-background-color: linear-gradient(to right, #3D5A4D, #52796F); -fx-background-radius: 30;");
        
        Pane hexagonBackgroundPane = new Pane();
        hexagonBackgroundPane.setMouseTransparent(true);

        double hexRadius = 22; 
        double hSpacing = hexRadius * Math.sqrt(3);
        double vSpacing = hexRadius * 1.5;
        double baseCalculatedWidth = 1150; 

        for (double y = -hexRadius; y < 170 + hexRadius; y += vSpacing) {
            boolean rowOffset = ((int)(y / vSpacing) % 2 == 0);
            for (double x = -hexRadius; x < baseCalculatedWidth + hexRadius; x += hSpacing) {
                double finalX = x + (rowOffset ? hSpacing / 2 : 0);
                double factorOpacidad = 1.0 - (finalX / baseCalculatedWidth);
                double calculatedOpacity = 0.01 + (Math.max(0, Math.min(1, factorOpacidad)) * 0.12);
                
                HexagonPolygon hex = new HexagonPolygon(hexRadius, calculatedOpacity);
                hex.setLayoutX(finalX); 
                hex.setLayoutY(y);
                
                hexagonBackgroundPane.getChildren().add(hex);
                
                RotateTransition rt = new RotateTransition(Duration.seconds(14 + (Math.random() * 8)), hex);
                rt.setByAngle(360); 
                rt.setInterpolator(Interpolator.LINEAR);
                rt.setCycleCount(Animation.INDEFINITE); 
                rt.play();
            }
        }
        
        Rectangle bannerClip = new Rectangle();
        bannerClip.setArcWidth(60);
        bannerClip.setArcHeight(60);
        bannerContainer.layoutBoundsProperty().addListener((obs, oldVal, newVal) -> {
            bannerClip.setWidth(newVal.getWidth());
            bannerClip.setHeight(newVal.getHeight());
        });
        bannerContainer.setClip(bannerClip);
        
        bannerBackground.getChildren().add(hexagonBackgroundPane);
        
        HBox topBannerContent = new HBox();
        topBannerContent.setPadding(new Insets(20, 40, 20, 40));
        topBannerContent.setAlignment(Pos.CENTER_LEFT);
        
        VBox greetBox = new VBox(12);
        greetBox.setAlignment(Pos.CENTER_LEFT);
        Label lblGreet = new Label(getDynamicGreetingText());
        lblGreet.setStyle("-fx-text-fill: white; -fx-font-size: 34; -fx-font-weight: bold;");
        
        xpBar = new ProgressBar(ActividadManager.getInstance().calcularProgresoDelDia());
        xpBar.setPrefWidth(300); 
        xpBar.setPrefHeight(10);
        xpBar.setStyle("-fx-accent: #B38E5D; -fx-control-inner-background: rgba(255,255,255,0.15); -fx-background-radius: 10; -fx-border-radius: 10; -fx-padding: 0;");
        greetBox.getChildren().addAll(lblGreet, xpBar);
        
        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);
        
        VBox clockContainer = new VBox(-10);
        clockContainer.setAlignment(Pos.CENTER_RIGHT);
        Label lblClock = new Label();
        lblClock.setStyle("-fx-text-fill: rgba(255, 255, 255, 0.9); -fx-font-size: 90; -fx-font-weight: 100; -fx-font-family: 'Segoe UI Light', 'Helvetica Neue', 'Arial'; -fx-letter-spacing: -3;");
        
        Label lblDateGlass = new Label();
        lblDateGlass.setStyle("-fx-text-fill: rgba(255, 255, 255, 0.7); -fx-font-size: 16; -fx-font-weight: 300; -fx-font-family: 'Segoe UI Light'; -fx-text-transform: uppercase; -fx-letter-spacing: 2;");
        
        InnerShadow innerGlow = new InnerShadow(2, 1, 1, Color.rgb(255, 255, 255, 0.4));
        DropShadow glassShadow = new DropShadow(15, 0, 6, Color.rgb(0, 0, 0, 0.25));
        glassShadow.setInput(innerGlow);
        lblClock.setEffect(glassShadow);
        lblDateGlass.setEffect(glassShadow);
        
        initClock(lblClock, lblDateGlass);
        clockContainer.getChildren().addAll(lblClock, lblDateGlass);
        topBannerContent.getChildren().addAll(greetBox, spacer, clockContainer);
        bannerContainer.getChildren().addAll(bannerBackground, topBannerContent);

        // 3. GALLERY VIEW (REJILLA 3 Y 3) 
        GridPane galleryGrid = new GridPane();
        galleryGrid.setHgap(25);
        galleryGrid.setVgap(25);
        galleryGrid.setAlignment(Pos.CENTER);

        galleryGrid.add(createSectionCard("notas", "Tus apuntes", "/images/card_notes.jpg", -50), 0, 0);
        galleryGrid.add(createSectionCard("agenda", "Horario semanal", "/images/card_agenda.jpg", -140), 1, 0);
        galleryGrid.add(createSectionCard("tareas", "Lista de pendientes", "/images/card_tasks.jpg", -90), 2, 0);
        
        galleryGrid.add(createSectionCard("pomodoro", "Concentración", "/images/card_pomodoro.jpg", 0), 0, 1);
        galleryGrid.add(createSectionCard("logros", "XP y rachas", "/images/card_achievements.jpg", -100), 1, 1);
        galleryGrid.add(createSectionCard("recursos", "Material de apoyo", "/images/card_resources.jpg", -60), 2, 1);

        // 4. SECCIÓN MONITOR DE SISTEMA 
        VBox currentlyPane = new VBox(15);
        currentlyPane.setPadding(new Insets(25));
        currentlyPane.setStyle("-fx-background-color: white; -fx-background-radius: 25; -fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.04), 10, 0, 0, 4);");
        
        Label lblCurrentlyTitle = new Label("✨ En este momento...");
        lblCurrentlyTitle.setStyle("-fx-font-size: 18; -fx-font-weight: bold; -fx-text-fill: #3D5A4D; -fx-font-family: 'Segoe UI';");
        
        GridPane currentlyGrid = new GridPane();
        currentlyGrid.setHgap(40);
        currentlyGrid.setVgap(18);
        currentlyGrid.setAlignment(Pos.CENTER_LEFT);

        Label lblMusicHead = new Label("🎵 Escuchando:");
        lblMusicHead.setStyle("-fx-font-size: 14; -fx-text-fill: #555; -fx-font-weight: 500;");
        Label lblMusicTrack = new Label("Detectando reproductor activo...");
        lblMusicTrack.setStyle("-fx-font-size: 14; -fx-font-weight: bold; -fx-text-fill: #1B263B; -fx-cursor: hand;");
        
        startSystemMediaTracker(lblMusicTrack);
        currentlyGrid.add(lblMusicHead, 0, 0);
        currentlyGrid.add(lblMusicTrack, 1, 0);

        Label lblReadingHead = new Label("📖 Leyendo:");
        lblReadingHead.setStyle("-fx-font-size: 14; -fx-text-fill: #555; -fx-font-weight: 500;");
        lblCurrentBook = new Label("Seleccionar documento de estudio...");
        lblCurrentBook.setStyle("-fx-font-size: 14; -fx-font-weight: bold; -fx-text-fill: #3D5A4D; -fx-underline: true; -fx-cursor: hand;");
        
        btnResumeBook = new Button("Continuar leyendo");
        btnResumeBook.setStyle("-fx-background-color: #E9EDC9; -fx-text-fill: #3D5A4D; -fx-background-radius: 10; -fx-font-size: 12; -fx-font-weight: bold; -fx-cursor: hand;");
        btnResumeBook.setVisible(false);

        String lastBookPath = prefs.get("LAST_BOOK_PATH", "");
        if (!lastBookPath.isEmpty()) {
            File file = new File(lastBookPath);
            if (file.exists()) {
                lblCurrentBook.setText(file.getName() + " (Pág. " + prefs.getInt("LAST_BOOK_PAGE", 1) + ")");
                lblCurrentBook.setStyle("-fx-font-size: 14; -fx-font-weight: bold; -fx-text-fill: #1B263B; -fx-underline: false; -fx-cursor: hand;");
                btnResumeBook.setVisible(true);
            }
        }

        lblCurrentBook.setOnMouseClicked(e -> {
            var fileChooser = new javafx.stage.FileChooser();
            fileChooser.setTitle("Seleccionar documento de estudio (PDF)");
            fileChooser.getExtensionFilters().add(new javafx.stage.FileChooser.ExtensionFilter("Archivos PDF", "*.pdf"));
            File selectedFile = fileChooser.showOpenDialog(stage);
            if (selectedFile != null) {
                prefs.put("LAST_BOOK_PATH", selectedFile.getAbsolutePath());
                prefs.putInt("LAST_BOOK_PAGE", 1);
                lblCurrentBook.setText(selectedFile.getName() + " (Pág. 1)");
                lblCurrentBook.setStyle("-fx-font-size: 14; -fx-font-weight: bold; -fx-text-fill: #1B263B; -fx-underline: false; -fx-cursor: hand;");
                btnResumeBook.setVisible(true);
                openSystemFileAsync(selectedFile);
            }
        });

        btnResumeBook.setOnAction(e -> {
            String path = prefs.get("LAST_BOOK_PATH", "");
            if (!path.isEmpty()) {
                File file = new File(path);
                if (file.exists()) {
                    openSystemFileAsync(file);
                    int currentPage = prefs.getInt("LAST_BOOK_PAGE", 1) + 1;
                    prefs.putInt("LAST_BOOK_PAGE", currentPage);
                    lblCurrentBook.setText(file.getName() + " (Pág. " + currentPage + ")");
                } else {
                    lblCurrentBook.setText("Archivo no encontrado o movido");
                    btnResumeBook.setVisible(false);
                }
            }
        });

        HBox readingBox = new HBox(15, lblCurrentBook, btnResumeBook);
        readingBox.setAlignment(Pos.CENTER_LEFT);
        currentlyGrid.add(lblReadingHead, 0, 1);
        currentlyGrid.add(readingBox, 1, 1);

        Label lblWorkingHead = new Label("💻 Trabajando en:");
        lblWorkingHead.setStyle("-fx-font-size: 14; -fx-text-fill: #555; -fx-font-weight: 500;");
        Label lblTaskLink = new Label("Proyecto de compilador JODA - Sprint 2");
        lblTaskLink.setStyle("-fx-font-weight: bold; -fx-font-size: 14; -fx-text-fill: #3D5A4D; -fx-underline: true; -fx-cursor: hand;");
        currentlyGrid.add(lblWorkingHead, 0, 2);
        currentlyGrid.add(lblTaskLink, 1, 2);

        currentlyPane.getChildren().addAll(lblCurrentlyTitle, currentlyGrid);

        VBox agendaPane = new VBox(15);
        agendaPane.setPadding(new Insets(25));
        agendaPane.setStyle("-fx-background-color: rgba(255, 255, 255, 0.45); " +
                            "-fx-background-radius: 30; " +
                            "-fx-border-color: rgba(255, 255, 255, 0.6); " +
                            "-fx-border-width: 1.5; " +
                            "-fx-border-radius: 30; " +
                            "-fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.05), 15, 0, 0, 5);");

        Label lblAgendaTitle = new Label("📋 Vista rápida de actividades de hoy");
        lblAgendaTitle.setStyle("-fx-font-size: 18; -fx-font-weight: bold; -fx-text-fill: #3D5A4D; -fx-font-family: 'Segoe UI';");

        TableView<Actividad> tableActivities = new TableView<>();
        tableActivities.setColumnResizePolicy(TableView.CONSTRAINED_RESIZE_POLICY);
        
        int totalItems = ActividadManager.getInstance().getActividadesDelDia().size();
        double calculatedHeight = (totalItems * 48) + 60; 
        tableActivities.setPrefHeight(calculatedHeight);
        tableActivities.setMinHeight(calculatedHeight);
        tableActivities.setMaxHeight(calculatedHeight);
        tableActivities.setStyle("-fx-background-color: transparent;");

        tableActivities.setRowFactory(tv -> {
            TableRow<Actividad> row = new TableRow<>();
            row.setOnDragDetected(event -> {
                if (!row.isEmpty()) {
                    Actividad actividad = row.getItem();
                    Dragboard db = row.startDragAndDrop(TransferMode.COPY);
                    ClipboardContent content = new ClipboardContent();
                    content.putString(actividad.getNombre() + " [" + actividad.getTipo() + "]");
                    db.setContent(content);
                    event.consume();
                }
            });
            return row;
        });

        TableColumn<Actividad, String> colNombre = new TableColumn<>("actividad");
        colNombre.setCellValueFactory(new PropertyValueFactory<>("nombre"));
        colNombre.setStyle("-fx-font-size: 14; -fx-font-weight: 500; -fx-alignment: CENTER-LEFT; -fx-padding: 0 0 0 15;");

        TableColumn<Actividad, String> colTipo = new TableColumn<>("tipo");
        colTipo.setCellValueFactory(new PropertyValueFactory<>("tipo"));
        colTipo.setCellFactory(column -> new TableCell<>() {
            @Override
            protected void updateItem(String item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) {
                    setGraphic(null);
                } else {
                    Label badge = new Label(item);
                    badge.setPadding(new Insets(5, 15, 5, 15));
                    badge.setFont(javafx.scene.text.Font.font("Segoe UI", javafx.scene.text.FontWeight.BOLD, 11));
                    switch (item.toLowerCase()) {
                        case "estudio": badge.setStyle("-fx-background-color: #E2ECE9; -fx-text-fill: #2D6A4F; -fx-background-radius: 12;"); break;
                        case "cultural": badge.setStyle("-fx-background-color: #E0EBF1; -fx-text-fill: #2B6CB0; -fx-background-radius: 12;"); break;
                        case "personal": badge.setStyle("-fx-background-color: #F7EBE6; -fx-text-fill: #C05621; -fx-background-radius: 12;"); break;
                        case "reunión": badge.setStyle("-fx-background-color: #EDE7F6; -fx-text-fill: #673AB7; -fx-background-radius: 12;"); break;
                        case "deporte": badge.setStyle("-fx-background-color: #FFF3E0; -fx-text-fill: #E65100; -fx-background-radius: 12;"); break;
                        default: badge.setStyle("-fx-background-color: #EEEEEE; -fx-text-fill: #616161; -fx-background-radius: 12;"); break;
                    }
                    setGraphic(badge); setAlignment(Pos.CENTER);
                }
            }
        });

        TableColumn<Actividad, LocalTime> colHora = new TableColumn<>("hora");
        colHora.setCellValueFactory(new PropertyValueFactory<>("horaVencimiento"));
        colHora.setCellFactory(column -> new TableCell<>(){
            private final DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("hh:mm a");
            @Override
            protected void updateItem(LocalTime item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) { setText(null); } 
                else {
                    setText(item.format(timeFormatter));
                    setStyle("-fx-font-size: 13; -fx-text-fill: #4A4A4A; -fx-font-weight: 600;");
                    setAlignment(Pos.CENTER);
                }
            }
        });

        TableColumn<Actividad, Boolean> colHecho = new TableColumn<>("echo");
        colHecho.setCellValueFactory(cellData -> new SimpleObjectProperty<>(cellData.getValue().isHecho()));
        colHecho.setCellFactory(column -> new TableCell<>() {
            private final Circle statusCircle = new Circle(8);
            { statusCircle.setEffect(new DropShadow(3, 0, 1.5, Color.rgb(0, 0, 0, 0.12))); }
            @Override
            protected void updateItem(Boolean hecho, boolean empty) {
                super.updateItem(hecho, empty);
                if (empty || hecho == null) { setGraphic(null); } 
                else {
                    if (hecho) {
                        statusCircle.setFill(Color.web("#3D5A4D"));
                        statusCircle.setStroke(Color.web("#2D4439"));
                        statusCircle.setStrokeWidth(1);
                    } else {
                        statusCircle.setFill(Color.web("#FFFFFF", 0.3));
                        statusCircle.setStroke(Color.web("#ccc"));
                        statusCircle.setStrokeWidth(2);
                    }
                    setGraphic(statusCircle); setAlignment(Pos.CENTER);
                }
            }
        });

        tableActivities.getColumns().addAll(colNombre, colTipo, colHora, colHecho);
        tableActivities.setItems(ActividadManager.getInstance().getActividadesDelDia());
        agendaPane.getChildren().addAll(lblAgendaTitle, tableActivities);

        VBox institutionalFooter = createAnimatedShieldFooter();

        mainContent.getChildren().addAll(bannerContainer, new Label("  📂 home / Gallery view"), galleryGrid, currentlyPane, agendaPane, institutionalFooter);

        root.setLeft(sidebar);
        root.setCenter(scroll);
        mainRoot.getChildren().add(root);

        btnChatToggle = new Button("💬");
        btnChatToggle.setStyle("-fx-background-color: #3D5A4D; -fx-text-fill: white; -fx-font-size: 24; -fx-background-radius: 50; " +
                               "-fx-pref-width: 60; -fx-pref-height: 60; -fx-cursor: hand; " +
                               "-fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.25), 12, 0, 0, 6);");
        btnChatToggle.setTranslateX(550); btnChatToggle.setTranslateY(320);

        btnChatToggle.setOnMousePressed(evt -> {
            dragStartX = evt.getSceneX() - btnChatToggle.getTranslateX();
            dragStartY = evt.getSceneY() - btnChatToggle.getTranslateY();
        });
        btnChatToggle.setOnMouseDragged(evt -> {
            btnChatToggle.setTranslateX(evt.getSceneX() - dragStartX);
            btnChatToggle.setTranslateY(evt.getSceneY() - dragStartY);
            if (isChatOpen) {
                chatWindow.setTranslateX(btnChatToggle.getTranslateX() - 160);
                chatWindow.setTranslateY(btnChatToggle.getTranslateY() - 270);
            }
        });
        btnChatToggle.setOnMouseClicked(evt -> { if (evt.isStillSincePress()) toggleChatWindow(); });

        // --- 8. VENTANA DEL CHAT ---
        chatWindow = new VBox(10);
        chatWindow.setMaxSize(380, 480);
        chatWindow.setPadding(new Insets(15));
        chatWindow.setStyle("-fx-background-color: rgba(255, 255, 255, 0.98); -fx-background-radius: 20; " +
                            "-fx-border-color: #ccc; -fx-border-radius: 20; -fx-border-width: 1; " +
                            "-fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.15), 20, 0, 0, 8);");
        chatWindow.setVisible(false); chatWindow.setOpacity(0);

        HBox chatHeader = new HBox();
        chatHeader.setAlignment(Pos.CENTER_LEFT);
        chatHeader.setStyle("-fx-padding: 0 0 5 0; -fx-border-color: #eee; -fx-border-width: 0 0 1 0;");
        Label lblChatTitle = new Label("Optem Inteligencia Artificial");
        lblChatTitle.setStyle("-fx-font-weight: bold; -fx-font-size: 14; -fx-text-fill: #3D5A4D;");
        Region headerSpacer = new Region(); HBox.setHgrow(headerSpacer, Priority.ALWAYS);
        Button btnCloseChat = new Button("✕");
        btnCloseChat.setStyle("-fx-background-color: transparent; -fx-text-fill: #888; -fx-font-size: 14; -fx-cursor: hand;");
        chatHeader.getChildren().addAll(chatPicContainer(), lblChatTitle, headerSpacer, btnCloseChat);

        txtChatHistory = new TextArea();
        txtChatHistory.setEditable(false); txtChatHistory.setWrapText(true);
        VBox.setVgrow(txtChatHistory, Priority.ALWAYS);
        txtChatHistory.setStyle("-fx-control-inner-background: #f8f9fa; -fx-background-color: transparent; -fx-text-fill: #333; -fx-font-size: 13;");
        txtChatHistory.appendText("Optem Bot: ¡Hola! Soy tu asistente de Inteligencia Artificial. Puedes arrastrar cualquier actividad de la tabla aquí para analizarla en profundidad. 🚀\n\n");

        txtChatHistory.setOnDragOver(evt -> { if (evt.getDragboard().hasString()) evt.acceptTransferModes(TransferMode.COPY); evt.consume(); });
        txtChatHistory.setOnDragDropped(evt -> {
            Dragboard db = evt.getDragboard();
            boolean success = false;
            if (db.hasString()) {
                String datosActividad = db.getString(); 
                txtChatHistory.appendText("Tú: [Arrastró Actividad] " + datosActividad + "\n");
                String respuestaAnalisis = procesarActividadArrastrada(datosActividad);
                Platform.runLater(() -> {
                    txtChatHistory.appendText("Optem Bot: " + respuestaAnalisis + "\n\n");
                    txtChatHistory.setScrollTop(Double.MAX_VALUE);
                });
                success = true;
            }
            evt.setDropCompleted(success); evt.consume();
        });

        HBox chatInputArea = new HBox(8);
        TextField txtChatInput = new TextField();
        txtChatInput.setPromptText("Escribe, pide recursos o arrastra una tarea aquí...");
        HBox.setHgrow(txtChatInput, Priority.ALWAYS);
        txtChatInput.setStyle("-fx-background-radius: 12; -fx-padding: 8 12; -fx-border-color: #ddd; -fx-border-radius: 12;");
        Button btnSendChat = new Button("➤");
        btnSendChat.setStyle("-fx-background-color: #3D5A4D; -fx-text-fill: white; -fx-background-radius: 12; -fx-pref-width: 40; -fx-cursor: hand;");

        chatInputArea.getChildren().addAll(txtChatInput, btnSendChat);
        chatWindow.getChildren().addAll(chatHeader, txtChatHistory, chatInputArea);
        mainRoot.getChildren().addAll(chatWindow, btnChatToggle);

        Runnable ejecutarEnvio = () -> {
            String prompt = txtChatInput.getText().trim();
            if (!prompt.isEmpty()) {
                txtChatHistory.appendText("Tú: " + prompt + "\n"); txtChatInput.clear();
                String respuestaBot = obtenerRespuestaDinamicaConRecursos(prompt);
                Thread simThread = new Thread(() -> {
                    try { Thread.sleep(500); } catch (Exception ex) {}
                    Platform.runLater(() -> {
                        txtChatHistory.appendText("Optem Bot: " + respuestaBot + "\n\n");
                        txtChatHistory.setScrollTop(Double.MAX_VALUE);
                    });
                });
                simThread.setDaemon(true); simThread.start();
            }
        };

        btnSendChat.setOnAction(e -> ejecutarEnvio.run());
        txtChatInput.setOnAction(e -> ejecutarEnvio.run());
        btnCloseChat.setOnAction(e -> toggleChatWindow());

        Scene scene = new Scene(mainRoot, 1300, 850);
        
        // ESTILOS CSS AVANZADOS 
        scene.getStylesheets().add("data:text/css," +
            ".table-view { -fx-background-color: transparent; -fx-padding: 5; }" +
            ".table-view .column-header-background { -fx-background-color: transparent; -fx-padding: 0 0 15 0; }" +
            ".table-view .column-header { -fx-background-color: rgba(220, 225, 222, 0.7); -fx-background-radius: 15; -fx-padding: 8; -fx-margin: 0 5 0 5; }" +
            ".table-view .column-header .label { -fx-text-fill: #3D5A4D; -fx-font-weight: bold; -fx-font-size: 13; -fx-alignment: CENTER; }" +
            ".table-row-cell { -fx-background-color: transparent; -fx-border-color: rgba(0,0,0,0.03); -fx-border-width: 0 0 1 0; -fx-padding: 8; }" +
            ".table-row-cell:filled:selected { -fx-background-color: #E9EDC9 !important; -fx-background-radius: 10; }" +
            ".table-row-cell:filled:selected .table-cell { -fx-text-fill: #3D5A4D !important; -fx-font-weight: bold; }" +
            ".table-view .scroll-bar:vertical { -fx-opacity: 0; -fx-pref-width: 0; -fx-padding: 0; }" +
            ".table-view .scroll-bar:horizontal { -fx-opacity: 0; -fx-pref-height: 0; -fx-padding: 0; }" +
            ".scroll-pane { -fx-background-color: transparent; -fx-background: transparent; -fx-border-color: transparent; }" +
            ".scroll-pane > .scroll-bar:vertical { -fx-background-color: transparent; -fx-pref-width: 8; }" +
            ".scroll-pane > .scroll-bar:vertical > .track { -fx-background-color: rgba(0, 0, 0, 0.03); -fx-background-radius: 10; }" +
            ".scroll-pane > .scroll-bar:vertical > .thumb { -fx-background-color: rgba(61, 90, 77, 0.4); -fx-background-radius: 10; }" +
            ".scroll-pane > .scroll-bar:vertical > .thumb:hover { -fx-background-color: rgba(61, 90, 77, 0.7); }" +
            ".scroll-pane > .scroll-bar:vertical > .increment-button, .scroll-pane > .scroll-bar:vertical > .decrement-button { -fx-padding: 0; -fx-shape: ''; }" +
            ".progress-bar .bar { -fx-background-radius: 10; }" +
            ".progress-bar .track { -fx-background-radius: 10; -fx-background-color: rgba(255, 255, 255, 0.15); -fx-border-color: transparent; }" +
            ".text-area .scroll-pane { -fx-background-color: transparent; }");

        stage.setOnCloseRequest(e -> { if (mediaTrackerTimeline != null) mediaTrackerTimeline.stop(); });
        stage.setScene(scene); stage.setMaximized(true); stage.show();
    }

    // PIE DE PÁGINA CON ESCUDO OFICIAL ANIMADO 
    private VBox createModulatedShieldFooter() {
        VBox footerRoot = new VBox(15);
        footerRoot.setAlignment(Pos.CENTER);
        footerRoot.setPadding(new Insets(35, 0, 20, 0));

        try {
            InputStream is = getClass().getResourceAsStream("/images/escudo_uaemex.png");
            if (is != null) {
                ImageView ivEscudo = new ImageView(new Image(is));
                ivEscudo.setPreserveRatio(true);
                ivEscudo.setFitHeight(110); 

                // EFECTO RESPIRACIÓN LENTO
                FadeTransition breathingAnimation = new FadeTransition(Duration.seconds(4.5), ivEscudo);
                breathingAnimation.setFromValue(0.05); // Nivel mínimo 
                breathingAnimation.setToValue(0.70);  // Visibilidad máxima
                breathingAnimation.setCycleCount(Animation.INDEFINITE);
                breathingAnimation.setAutoReverse(true);
                breathingAnimation.setInterpolator(Interpolator.EASE_BOTH); 
                breathingAnimation.play();

                footerRoot.getChildren().add(ivEscudo);
            }
        } catch (Exception ex) {
            Label lblFallback = new Label("UNIVERSIDAD AUTÓNOMA DEL ESTADO DE MÉXICO");
            lblFallback.setStyle("-fx-text-fill: rgba(61, 90, 77, 0.4); -fx-font-weight: bold; -fx-font-size: 13; -fx-letter-spacing: 2;");
            footerRoot.getChildren().add(lblFallback);
        }

        return footerRoot;
    }

    // Método alternativo por coincidencia de firma para blindar la inicialización en caliente
    private VBox createAnimatedShieldFooter() {
        return createModulatedShieldFooter();
    }

    private String procesarActividadArrastrada(String datos) {
        String dataLower = datos.toLowerCase();
        StringBuilder sb = new StringBuilder();
        sb.append("He leído con éxito la actividad arrastrada:\n");
        sb.append("Clasificación:").append(datos).append("\n\n");
        if (dataLower.contains("bnf") || dataLower.contains("parser") || dataLower.contains("compiladores") || dataLower.contains("joda")) {
            sb.append("Resumen (Compiladores):\n")
              .append("Estás procesando las reglas de producción sintáctica para tu lenguaje. Evita bucles recursivos por la izquierda.\n\n")
              .append("Recursos Recomendados:\n")
              .append("- Lectura: Sección de Gramáticas Independientes del Contexto (Libro de C. Fischer).");
        } else {
            sb.append("Resumen:\n")
              .append("Actividad académica regular agendada para el día de hoy.\n\n")
              .append("Sugerencia:\n")
              .append("Utiliza un bloque de enfoque Pomodoro de 25 minutos.");
        }
        return sb.toString();
    }

    private String obtenerRespuestaDinamicaConRecursos(String consulta) {
        String query = consulta.toLowerCase();
        if (query.contains("ayuda") || query.contains("recursos")) {
            return "¡Por supuesto! Analizando tu carga de trabajo, te recomiendo revisar el libro de C. Fischer en tu sección de Material de Apoyo.";
        }
        if (query.contains("hola")) {
            return "¡Hola! Estoy listo. Puedes escribirme tus dudas sobre cualquier clase o arrastrar una tarea directamente aquí.";
        }
        return "Entendido. He procesado tu consulta dentro del contexto de Optem.";
    }

    private void toggleChatWindow() {
        isChatOpen = !isChatOpen;
        if (isChatOpen) {
            chatWindow.setTranslateX(btnChatToggle.getTranslateX() - 160);
            chatWindow.setTranslateY(btnChatToggle.getTranslateY() - 270);
            chatWindow.setVisible(true);
            FadeTransition fadeIn = new FadeTransition(Duration.millis(200), chatWindow);
            fadeIn.setToValue(1.0); fadeIn.play();
        } else {
            FadeTransition fadeOut = new FadeTransition(Duration.millis(150), chatWindow);
            fadeOut.setToValue(0.0); fadeOut.setOnFinished(evt -> chatWindow.setVisible(false));
            fadeOut.play();
        }
    }

    private StackPane chatPicContainer() {
        StackPane container = new StackPane(); container.setPadding(new Insets(0, 8, 0, 0));
        Circle pic = new Circle(12, Color.web("#3D5A4D"));
        Label letter = new Label("O"); letter.setStyle("-fx-text-fill: white; -fx-font-size: 10; -fx-font-weight: bold;");
        container.getChildren().addAll(pic, letter); return container;
    }

    private void startSystemMediaTracker(Label label) {
        mediaTrackerTimeline = new Timeline(new KeyFrame(Duration.ZERO, e -> {
            Thread processThread = new Thread(() -> {
                try {
                    Process process = Runtime.getRuntime().exec("tasklist /v /fo csv");
                    BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                    String line; String activeTrack = "Ningún contenido multimedia en reproducción";
                    while ((line = reader.readLine()) != null) {
                        if (line.contains("Spotify.exe") && line.contains(",")) {
                            String[] parts = line.split("\",\"");
                            if (parts.length > 8) {
                                String title = parts[8].replace("\"", "");
                                if (!title.equalsIgnoreCase("Spotify") && !title.equalsIgnoreCase("GDI+ Window")) {
                                    activeTrack = title + " 🎵"; break;
                                }
                            }
                        }
                    }
                    final String finalTrack = activeTrack;
                    Platform.runLater(() -> label.setText(finalTrack));
                } catch (Exception ex) { Platform.runLater(() -> label.setText("lo-fi hip hop 🎵")); }
            });
            processThread.setDaemon(true); processThread.start();
        }), new KeyFrame(Duration.seconds(5)));
        mediaTrackerTimeline.setCycleCount(Animation.INDEFINITE); mediaTrackerTimeline.play();
    }

    private void openSystemFileAsync(File file) {
        Thread openThread = new Thread(() -> {
            try {
                if (!file.exists()) return;
                if (java.awt.Desktop.isDesktopSupported() && java.awt.Desktop.getDesktop().isSupported(java.awt.Desktop.Action.OPEN)) {
                    java.awt.Desktop.getDesktop().open(file);
                }
            } catch (Exception e) {}
        });
        openThread.setDaemon(true); openThread.start();
    }

    private void toggleButtonTexts(boolean showText, Button... buttons) {
        for (Button btn : buttons) {
            String icon = (String) btn.getUserData();
            if (showText) { btn.setText(icon + "  " + btn.getId()); btn.setAlignment(Pos.CENTER_LEFT); }
            else { btn.setText(icon); btn.setAlignment(Pos.CENTER); }
        }
    }

    private Button createMenuButton(String icon, String text, boolean active) {
        Button btn = new Button(icon + "  " + text);
        btn.setId(text); btn.setUserData(icon); btn.setMaxWidth(Double.MAX_VALUE);
        btn.setAlignment(Pos.CENTER_LEFT);
        btn.setStyle("-fx-background-color: " + (active ? "#E9EDC9" : "transparent") + "; " +
                    "-fx-background-radius: 12; -fx-padding: 12 15; -fx-cursor: hand; " +
                    "-fx-text-fill: " + (active ? "#3D5A4D" : "#555") + "; -fx-font-weight: " + (active ? "bold" : "normal") + "; -fx-font-size: 14;");
        return btn;
    }

    private String getDynamicGreetingText() {
        int hora = LocalTime.now().getHour();
        if (hora >= 6 && hora < 12) return "¡Buenos días!";
        else if (hora >= 12 && hora < 19) return "¡Buenas tardes!";
        else return "¡Buenas noches!";
    }

    private void initClock(Label lblClock, Label lblDate) {
        DateTimeFormatter timeFmt = DateTimeFormatter.ofPattern("HH:mm");
        DateTimeFormatter dateFmt = DateTimeFormatter.ofPattern("EEEE, d 'de' MMMM", new Locale("es", "ES"));
        Timeline clock = new Timeline(new KeyFrame(Duration.ZERO, e -> {
            LocalDateTime now = LocalDateTime.now(); lblClock.setText(now.format(timeFmt)); lblDate.setText(now.format(dateFmt));
        }), new KeyFrame(Duration.seconds(1)));
        clock.setCycleCount(Animation.INDEFINITE); clock.play();
    }

    private VBox createSectionCard(String title, String sub, String imgPath, double offsetY) {
        VBox card = new VBox(0); card.setPrefSize(280, 210);
        card.setStyle("-fx-background-color: white; -fx-background-radius: 20; -fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.08), 12, 0, 0, 6); -fx-cursor: hand;");
        Pane imgContainer = new Pane(); imgContainer.setPrefSize(280, 130);
        try {
            InputStream is = getClass().getResourceAsStream(imgPath);
            if (is != null) {
                ImageView iv = new ImageView(new Image(is)); iv.setPreserveRatio(true); iv.setFitWidth(280); iv.setLayoutY(offsetY); 
                Rectangle clip = new Rectangle(280, 130); clip.setArcWidth(40); clip.setArcHeight(40);
                imgContainer.setClip(clip); imgContainer.getChildren().add(iv);
            }
        } catch(Exception e) { imgContainer.setStyle("-fx-background-color: #ddd; -fx-background-radius: 20 20 0 0;"); }
        VBox info = new VBox(3); info.setPadding(new Insets(12, 15, 12, 15));
        Label t = new Label("📁 " + title); t.setStyle("-fx-font-weight: bold; -fx-font-size: 15;");
        Label s = new Label(sub); s.setStyle("-fx-text-fill: #888; -fx-font-size: 12;");
        info.getChildren().addAll(t, s); card.getChildren().addAll(imgContainer, info);
        card.setOnMouseEntered(e -> card.setStyle(card.getStyle() + "-fx-translate-y: -5;"));
        card.setOnMouseExited(e -> card.setStyle(card.getStyle().replace("-fx-translate-y: -5;", "")));
        return card;
    }

    class HexagonPolygon extends Polygon {
        HexagonPolygon(double radius, double opacity) {
            for (int i = 0; i < 6; i++) {
                double angle = 2 * Math.PI / 6 * i;
                getPoints().addAll(radius * Math.cos(angle), radius * Math.sin(angle));
            }
            setFill(Color.web("#FFFFFF", opacity)); setStroke(Color.web("#FFFFFF", opacity * 1.5)); setStrokeWidth(1.2);
        }
    }
}