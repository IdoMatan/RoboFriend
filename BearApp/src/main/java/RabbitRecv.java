import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DeliverCallback;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;

import javax.swing.*;
import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeoutException;

public class RabbitRecv {
    ConnectionFactory factory = new ConnectionFactory();
    Channel channel;
    Connection connection;

    static final String EXCHANGE_NAME = "main";
    private final static String QUEUE_NAME = "BearApp";

    String routingKey = "video.action";

    Map<String, Object> message;


    public void initRabbit(JButton button) throws IOException, TimeoutException {
        this.factory.setUsername("rabbitmq");
        this.factory.setPassword("rabbitmq");
        this.factory.setHost("13.58.106.247");

        this.connection = factory.newConnection();
        this.channel = connection.createChannel();

        this.channel.exchangeDeclare(EXCHANGE_NAME, "topic");
        this.channel.queueDeclare("BearApp", false, false, false, null);
        channel.queueBind(this.QUEUE_NAME, this.EXCHANGE_NAME, this.routingKey);

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {

            ObjectMapper mapper = new ObjectMapper();

            String message_raw = new String(delivery.getBody(), "UTF-8");
            System.out.println(" [x] Received '" + message_raw + "'");
            try {
                this.message = mapper.readValue(message_raw, new TypeReference<Map<String, Object>>() {});
                System.out.println("time : " + this.message.get("time"));
                button.doClick();

            } catch (Exception e) {
//                e.printStackTrace();
            }
        };
        this.channel.basicConsume(this.QUEUE_NAME, true, deliverCallback, consumerTag -> { });

    }
    public String getAction(){
        return (String) this.message.get("action");
    }


}
