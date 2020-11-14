import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

public class RabbitSender {
    ConnectionFactory factory = new ConnectionFactory();
    Channel channel;
    Connection connection;
    static final String EXCHANGE_NAME = "main";
    String routingKey = "action";

    public void initRabbit() throws IOException, TimeoutException {
        this.factory.setUsername("rabbitmq");
        this.factory.setPassword("rabbitmq");
        this.factory.setHost("13.58.106.247");

        this.connection = factory.newConnection();
        this.channel = connection.createChannel();

        this.channel.exchangeDeclare(EXCHANGE_NAME, "topic");
        this.channel.queueDeclare("BearApp", false, false, false, null);
    }
}
