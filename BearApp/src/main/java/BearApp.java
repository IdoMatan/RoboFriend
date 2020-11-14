import com.google.common.base.Joiner;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;


import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.lang.reflect.Array;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.TimeoutException;

public class BearApp {
    private JButton foxStory;
    private JPanel mainPanel;
    private JButton apt2Rent;
    private JTextField userTextField;
    private JLabel userLabel;
    private JButton resetButton;
    private JButton stopButton;
    private JPanel storyPanel;
    private JPanel actionsSelector;
    private JButton nextPage;
    private JButton moveHand;
    private JButton moveHead;
    private JButton askQuestionButton;
    private JLabel sessionLabel;
    private JTextField sessionTextField;
    private JComboBox actor;
    private JButton showActions;
    private JPanel actionsPush;
    private JPanel textPanel;
    private JButton pauseButton;
    private JPanel inStory;
    private JPanel stopPanel;
    private JSONObject stories;
    private JSONObject story;
    private RabbitSender rabbit;
    private RabbitRecv rabbit_recv;
    SimpleDateFormat formatter;
    Date date;
    Process[] p = new Process[2];

    JFrame frame = new JFrame("BearApp");


    public void initBearApp(int width, int height ) throws IOException, TimeoutException {
        this.frame.setContentPane(new BearApp().mainPanel);
//        this.frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
        this.frame.pack();
        this.frame.setSize(width, height);
        this.frame.setVisible(true);
    }

    public void loadStoriesConfig(){
        JSONParser parser = new JSONParser();
        try {
            Object obj = parser.parse(new FileReader("/home/matanweks/Apps/RoboFriend/StoryConfig.json"));
            stories = (JSONObject) obj;
//            System.out.println(stories.toJSONString());
        } catch (ParseException | IOException parseException) {
            parseException.printStackTrace();
        }
    }

    public void initAppAppearance(){
        actionsSelector.setVisible(false);
        actionsPush.setVisible(false);
        inStory.setVisible(false);
        storyPanel.setVisible(true);
//            UIManager.setLookAndFeel("javax.swing.plaf.metal.MetalLookAndFeel");
    }

    public void initRubbit() throws IOException, TimeoutException {
        rabbit = new RabbitSender();
        rabbit.initRabbit();
        rabbit_recv = new RabbitRecv();
        rabbit_recv.initRabbit(showActions);
    }

    public void timeSetup(){
        formatter= new SimpleDateFormat("MM/dd/yyyy, HH:mm:ss");
        date = new Date(System.currentTimeMillis());
        System.out.println(formatter.format(date));
    }

//    public void initPythons(Process[] p){
    public void initPythons(){
        String command = "bash +x ./runPython.sh";
        try {
            p[0] = Runtime.getRuntime().exec(command);
//                    BufferedReader br = new BufferedReader(
//                            new InputStreamReader(p[0].getErrorStream()));
//                    String s;
//                    while ((s = br.readLine()) != null)
//                        System.out.println("line: " + s);
//                    p[0].waitFor();
////                    wait(1000);
//                    System.out.println ("exit: " + p[0].exitValue());
//                    p[0].destroy();
        } catch (IOException ioException) {
            ioException.printStackTrace();
        }
    }
    public void storyModeAppAppearance(){
        storyPanel.setVisible(false);
        inStory.setVisible(true);
    }

    public void sendAction(String action){
        actionsSelector.setVisible(false);
        date = new Date(System.currentTimeMillis());
        JSONObject massage = new JSONObject();
        massage.put("time", formatter.format(date));
        massage.put("action", action);
        massage.put("story", null);
        try {
            rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
        } catch (IOException ioException) {
            ioException.printStackTrace();
        }
    }

    public BearApp() throws IOException, TimeoutException {
        this.initAppAppearance();
        this.initRubbit();
        this.loadStoriesConfig();
        this.timeSetup();
        this.initPythons();

//---------------- closing  routine --------------------------------------------------------------------------------------------
        frame.addWindowListener(new WindowListener() {
            @Override
            public void windowOpened(WindowEvent e) {}
            @Override
            public void windowClosing(WindowEvent e) {
                date = new Date(System.currentTimeMillis());
                JSONObject massage = new JSONObject();
                massage.put("time", formatter.format(date));
                massage.put("action", "EOS");
                massage.put("username", userTextField.getText());
                massage.put("session", sessionTextField.getText());
                massage.put("manual", actor.getSelectedItem());
                try {
                    rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
                } catch (IOException ioException) {
                    ioException.printStackTrace();
                }
                String command = "bash +x ./killPython.sh";
                try {
                    p[1] = Runtime.getRuntime().exec(command);
                    p[1].waitFor();
                } catch (IOException | InterruptedException ioException) {
                    ioException.printStackTrace();
                }
                p[0].destroy();
                p[1].destroy();
                System.exit(0);
            }

            @Override
            public void windowClosed(WindowEvent e) {}

            @Override
            public void windowIconified(WindowEvent e) {}

            @Override
            public void windowDeiconified(WindowEvent e) {}

            @Override
            public void windowActivated(WindowEvent e) {}

            @Override
            public void windowDeactivated(WindowEvent e) {}
        });

//---------------- Stories buttons --------------------------------------------------------------------------------------------

        foxStory.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                storyModeAppAppearance();
                story = (JSONObject) stories.get("FoxStory");
//                List<String> actions = (List<String>) story.get("acitions");
//                System.out .println(actions.get(0));
//                List yourJson = (List) story.get("actions");
                date = new Date(System.currentTimeMillis());
                JSONObject massage = new JSONObject();
                massage.put("time", formatter.format(date));
                massage.put("action", "initial_start");
                massage.put("story_name", "FoxStory");
                massage.put("story", story.get("pages"));
                massage.put("username", userTextField.getText());
                massage.put("session", sessionTextField.getText());
                massage.put("manual", actor.getSelectedItem());
                try {
                    rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
                } catch (IOException ioException) {
                    ioException.printStackTrace();
                }
            }
        });

        apt2Rent.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                storyModeAppAppearance();
                story = (JSONObject) stories.get("AptForRent");
                System.out.println( story.get("actions"));
                date = new Date(System.currentTimeMillis());
                JSONObject massage = new JSONObject();
                massage.put("time", formatter.format(date));
                massage.put("action", "initial_start");
                massage.put("story_name", "AptForRent");
                massage.put("story", story.get("pages"));
                massage.put("username", userTextField.getText());
                massage.put("session", sessionTextField.getText());
                massage.put("manual", actor.getSelectedItem());
                try {
                    rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
                } catch (IOException ioException) {
                    ioException.printStackTrace();
                }
            }
//                String action = rabbit_recv.getAction();
//                System.out.println(action);
//                mainPanel.removeAll();
//                mainPanel.add(newPanel);

//                frame.getContentPane().removeAll();
//                frame.getContentPane().add(newPanel);
//                frame.pack();

//                System.out.println(rabbit_recv.message.get("action"));
//                textField1.setText((String) rabbit_recv.message.get("action"));
        });
//---------------- Stop reset --------------------------------------------------------------------------------------------

        stopButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                date = new Date(System.currentTimeMillis());
                JSONObject massage = new JSONObject();
                massage.put("time", formatter.format(date));
                massage.put("action", "EOS");
                massage.put("username", userTextField.getText());
                massage.put("session", sessionTextField.getText());
                massage.put("manual", actor.getSelectedItem());
                try {
                    rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
                } catch (IOException ioException) {
                    ioException.printStackTrace();
                }
                String command = "bash +x ./killPython.sh";
                try {
                    p[1] = Runtime.getRuntime().exec(command);
                    p[1].waitFor();
                } catch (IOException | InterruptedException ioException) {
                    ioException.printStackTrace();
                }
                p[0].destroy();
                p[1].destroy();
                System.exit(0);
            }
        });

//---------------- Actions --------------------------------------------------------------------------------------------
        nextPage.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {sendAction("Play next page");}
        });
        moveHand.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {sendAction("Wave hands");}
        });
        moveHead.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {sendAction("Move head");}
        });
        askQuestionButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                sendAction("Ask question");
            }
        });

//---------------- Utils buttons --------------------------------------------------------------------------------------------
        showActions.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                actionsSelector.setVisible(true);
            }
        });
        resetButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                initAppAppearance();
            }
        });
        pauseButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                String action;
                if (pauseButton.getText() == "Play"){
                    action = "pause";
                    pauseButton.setText("Pause");
                    Icon icon = new ImageIcon("/home/matanweks/Apps/RoboFriend/BearApp/src/main/resources/icons/pause_icon.png");
                    pauseButton.setIcon(icon);

                } else {
                    action = "play";
                    pauseButton.setText("Play");
                    Icon icon = new ImageIcon("/home/matanweks/Apps/RoboFriend/BearApp/src/main/resources/icons/play_icon.png");
                    pauseButton.setIcon(icon);
                }
                date = new Date(System.currentTimeMillis());
                JSONObject massage = new JSONObject();
                massage.put("time", formatter.format(date));
                massage.put("action", action);
                massage.put("story", null);

                try {
                    rabbit.channel.basicPublish(rabbit.EXCHANGE_NAME, rabbit.routingKey, null, massage.toJSONString().getBytes());
                } catch (IOException ioException) {
                    ioException.printStackTrace();
                }
            }
        });
    }


//---------------- Main --------------------------------------------------------------------------------------------

    public static void main(String[] args) throws IOException, TimeoutException {
        BearApp app = new BearApp();
        app.initBearApp(800, 400);
    }
}

