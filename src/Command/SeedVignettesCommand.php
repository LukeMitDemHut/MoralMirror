<?php

namespace App\Command;

use App\Entity\Vignette;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Style\SymfonyStyle;

#[AsCommand(
    name: 'app:seed-vignettes',
    description: 'Seed the database with EMCS vignettes',
)]
class SeedVignettesCommand extends Command
{
    public function __construct(
        private EntityManagerInterface $entityManager
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $io = new SymfonyStyle($input, $output);

        $vignettes = [
            // Socially Close Protagonists
            ['content' => 'I buy concert tickets on the internet for my brother and myself. I can get two seats side by side. However, the tickets fall into two different price categories, so that one ticket is 10 € more expensive than the other.', 'altruisticResponse' => 'I take the more expensive ticket.', 'egoisticResponse' => 'I take the cheaper ticket.', 'itemDifficulty' => 0.61, 'realitySimilarity' => 4.03, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I am just about to leave for work as a neighbor and friend rings my bell. She asks me if I could drive her to the doctor because she is not feeling well. I am already late and have a meeting with my boss today.', 'altruisticResponse' => 'I drive her to the doctor.', 'egoisticResponse' => 'I go to work.', 'itemDifficulty' => 0.50, 'realitySimilarity' => 4.10, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'Today, it is games night and I play poker for money with friends. As one of my opponents shortly gets distracted, I catch a glance of his/her cards. The other players do not notice anything.', 'altruisticResponse' => 'I let the cards be reshuffled.', 'egoisticResponse' => 'I keep playing.', 'itemDifficulty' => 0.17, 'realitySimilarity' => 4.77, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I have been single for quite a long time. Tonight, I finally have a promising date again. As I am about to leave, a good friend of mine who is not feeling well gives me a call and wants to meet up with me now.', 'altruisticResponse' => 'I meet up with my friend.', 'egoisticResponse' => 'I go on the date.', 'itemDifficulty' => 0.66, 'realitySimilarity' => 4.88, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'A friend of mine definitely wants to buy an old computer game from me that he loves playing. I promise to sell it to him for 20 € tomorrow. Later on, as I check on the internet, I see that I could sell the game immediately for 60 €.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I sell the game for more money.', 'itemDifficulty' => 0.79, 'realitySimilarity' => 4.14, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'I am talking to my aunt at a family celebration. All of a sudden, it comes to my mind that she lent me a CD last Christmas. She does not seem to remember anymore and I like the CD very much.', 'altruisticResponse' => 'I return the CD.', 'egoisticResponse' => 'I keep the CD.', 'itemDifficulty' => 0.74, 'realitySimilarity' => 4.78, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I have promised my sister to take care of her children tonight. Now, I realize that I am also invited to a farewell party today that is very important for me. I could think up an excuse to go to the party.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I think up an excuse.', 'itemDifficulty' => 0.70, 'realitySimilarity' => 4.80, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'A friend of mine has inherited a coin collection that interests me very much. He offers to sell the coins to me for a low price. The coins are actually worth considerably more money.', 'altruisticResponse' => 'I inform the friend about the value.', 'egoisticResponse' => 'I buy the coins for the low price.', 'itemDifficulty' => 0.62, 'realitySimilarity' => 3.67, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'A friend of mine and I are big fans of a band. The band is giving a concert in our hometown. At the ticket agency, I am only able to get one ticket.', 'altruisticResponse' => 'I give the ticket to my friend.', 'egoisticResponse' => 'I go to the concert myself.', 'itemDifficulty' => 0.62, 'realitySimilarity' => 3.68, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'While locking up my bike, it falls against a car. In the darkness, I do not detect any scratches. Next day, I hear my well-known neighbor complaining about a fresh scratch on his car.', 'altruisticResponse' => 'I inform the neighbor.', 'egoisticResponse' => 'I keep quiet about the incident.', 'itemDifficulty' => 0.56, 'realitySimilarity' => 4.48, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'It is the soccer world cup final match. I am a big fan. All of a sudden, a friend who is not feeling well calls and wants to meet up with me right now.', 'altruisticResponse' => 'I meet up with my friend.', 'egoisticResponse' => 'I watch the soccer game.', 'itemDifficulty' => 0.81, 'realitySimilarity' => 1.80, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'I promised my partner to go to a company party. Now I realize I urgently need the time to prepare for an important exam.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I prepare for the exam.', 'itemDifficulty' => 0.51, 'realitySimilarity' => 4.89, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'My mother gives me 20 € for pet food. It is on special offer and only costs 10 €. I have many expenses this month and could use the 10 € for myself.', 'altruisticResponse' => 'I return the money to my mother.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.77, 'realitySimilarity' => 5.11, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I get the last ticket for a concert. A classmate and friend standing behind me in line realizes this, is appalled, and bursts into tears.', 'altruisticResponse' => 'I give the ticket to him.', 'egoisticResponse' => 'I keep the ticket for myself.', 'itemDifficulty' => 0.61, 'realitySimilarity' => 3.57, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I promised my grandfather to help him with forms this evening. I suddenly win tickets for my favorite band\'s sold out concert tonight.', 'altruisticResponse' => 'I help my grandfather.', 'egoisticResponse' => 'I go to the concert.', 'itemDifficulty' => 0.45, 'realitySimilarity' => 3.80, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I am at the airport for a holiday. My mother calls to say my father had an accident and was admitted to the hospital.', 'altruisticResponse' => 'I cancel the holiday.', 'egoisticResponse' => 'I take the flight anyway.', 'itemDifficulty' => 0.41, 'realitySimilarity' => 4.47, 'set' => 'A', 'socialProximity' => 'close'],
            ['content' => 'I promised a neighbor and friend to receive an urgent parcel. It\'s 5 pm and the parcel hasn\'t arrived. My gym course starts soon.', 'altruisticResponse' => 'I wait for the parcel service.', 'egoisticResponse' => 'I go to the gym course.', 'itemDifficulty' => 0.43, 'realitySimilarity' => 4.86, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I promised to go to a friend\'s birthday party. It is the same day as my favorite band\'s concert. I could think up an excuse to go to the concert.', 'altruisticResponse' => 'I go to the birthday party.', 'egoisticResponse' => 'I think up an excuse.', 'itemDifficulty' => 0.83, 'realitySimilarity' => 1.34, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I want to sell my old laptop to my uncle for 200 €. I see on an internet portal that I could sell it for 300 €.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I sell the laptop for more money.', 'itemDifficulty' => 0.83, 'realitySimilarity' => 1.37, 'set' => 'B', 'socialProximity' => 'close'],
            ['content' => 'I promised my grandmother to take her to the doctor. One hour before, my boss calls me for an important meeting regarding my promotion.', 'altruisticResponse' => 'I take my grandmother to the doctor.', 'egoisticResponse' => 'I go to the meeting with my boss.', 'itemDifficulty' => 0.52, 'realitySimilarity' => 4.32, 'set' => 'A', 'socialProximity' => 'close'],

            // Socially Distant Protagonists
            ['content' => 'While pulling out of a supermarket parking space, I bump the car next to mine. It is dark and nobody saw anything.', 'altruisticResponse' => 'I leave a message for the owner.', 'egoisticResponse' => 'I drive away quickly.', 'itemDifficulty' => 0.79, 'realitySimilarity' => 5.73, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'After hours in a café, the waitress miscalculates the bill by 3 € in my favor.', 'altruisticResponse' => 'I return the money.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.61, 'realitySimilarity' => 5.55, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'I am boarding a train that runs once an hour. A man with crutches falls on the platform. If I help, I miss the train.', 'altruisticResponse' => 'I help the man.', 'egoisticResponse' => 'I take the train.', 'itemDifficulty' => 0.71, 'realitySimilarity' => 4.76, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'In a cocktail bar, the waiter forgot to bill my last cocktail.', 'altruisticResponse' => 'I point out the mistake.', 'egoisticResponse' => 'I pay without the last cocktail.', 'itemDifficulty' => 0.37, 'realitySimilarity' => 5.37, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'A buyer accidentally transfers 40 € too much for a computer I sold online.', 'altruisticResponse' => 'I transfer the money back.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.68, 'realitySimilarity' => 4.38, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'I am selling a car. I know the radiator needs urgent exchange, but the buyer doesn\'t notice.', 'altruisticResponse' => 'I mention the defect.', 'egoisticResponse' => 'I keep quiet about the defect.', 'itemDifficulty' => 0.72, 'realitySimilarity' => 4.69, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'In a supermarket parking lot, a woman\'s grocery bag bursts. If I help, I\'ll be late for an important appointment.', 'altruisticResponse' => 'I help the woman.', 'egoisticResponse' => 'I get into my car.', 'itemDifficulty' => 0.68, 'realitySimilarity' => 5.09, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'I agree to sell a wardrobe for 140 €. Later, someone else offers 200 €.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I sell the wardrobe for more money.', 'itemDifficulty' => 0.49, 'realitySimilarity' => 4.86, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'A woman\'s grocery bag falls as I\'m getting on a bus that runs every 30 minutes.', 'altruisticResponse' => 'I help the woman.', 'egoisticResponse' => 'I take the bus.', 'itemDifficulty' => 0.60, 'realitySimilarity' => 5.00, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'At supermarket checkout, the cashier gives me 4 € back instead of 2 € for an 8 € purchase.', 'altruisticResponse' => 'I return the money.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.62, 'realitySimilarity' => 5.67, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'Several items drop from a woman\'s purse as I\'m running for a bus that runs every hour. No one else is around to help.', 'altruisticResponse' => 'I help the woman.', 'egoisticResponse' => 'I run to the bus.', 'itemDifficulty' => 0.61, 'realitySimilarity' => 4.97, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'I find a 20 € bill on the ground. I see a homeless man going through dustbins nearby.', 'altruisticResponse' => 'I give the money to the man.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.41, 'realitySimilarity' => 3.83, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'I found a great apartment, but the landlord forbids pets and I have a hamster. The landlord lives 100 km away and likely won\'t find out.', 'altruisticResponse' => 'I do not take the apartment.', 'egoisticResponse' => 'I keep quiet about the pet.', 'itemDifficulty' => 0.42, 'realitySimilarity' => 4.76, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'A pizza delivery boy gives me 5 € too much in change.', 'altruisticResponse' => 'I return the money.', 'egoisticResponse' => 'I keep the money.', 'itemDifficulty' => 0.65, 'realitySimilarity' => 5.26, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'Selling a painting at a flea market for 100 €. While the buyer is at the bank, someone else offers 150 €.', 'altruisticResponse' => 'I keep my promise.', 'egoisticResponse' => 'I sell for the higher price.', 'itemDifficulty' => 0.71, 'realitySimilarity' => 4.33, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'An old woman stumbles and groceries roll away. My bus is leaving and only runs every two hours. I am the only one around.', 'altruisticResponse' => 'I help the woman.', 'egoisticResponse' => 'I take the bus.', 'itemDifficulty' => 0.56, 'realitySimilarity' => 4.29, 'set' => 'B', 'socialProximity' => 'distant'],
            ['content' => 'I find a wallet with 50 € but no ID. I could turn it into the lost and found office.', 'altruisticResponse' => 'I turn in the wallet.', 'egoisticResponse' => 'I keep the wallet.', 'itemDifficulty' => 0.66, 'realitySimilarity' => 4.80, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'I am driving to a meeting and am late. A slight rear-end collision happens in front of me. If I stop, I\'ll be late.', 'altruisticResponse' => 'I stop my car.', 'egoisticResponse' => 'I keep driving.', 'itemDifficulty' => 0.50, 'realitySimilarity' => 4.94, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'Pedestrian light is red, but my bus is leaving. A little boy is standing on the other side.', 'altruisticResponse' => 'I wait.', 'egoisticResponse' => 'I cross on red.', 'itemDifficulty' => 0.35, 'realitySimilarity' => 5.74, 'set' => 'A', 'socialProximity' => 'distant'],
            ['content' => 'I see a man on crutches struggling with a suitcase as I am getting on my train. If I help, I miss the train.', 'altruisticResponse' => 'I help the man.', 'egoisticResponse' => 'I get on the train.', 'itemDifficulty' => 0.63, 'realitySimilarity' => 4.83, 'set' => 'A', 'socialProximity' => 'distant'],
        ];

        foreach ($vignettes as $vignetteData) {
            $vignette = new Vignette();
            $vignette->setContent($vignetteData['content']);
            $vignette->setAltruisticResponse($vignetteData['altruisticResponse']);
            $vignette->setEgoisticResponse($vignetteData['egoisticResponse']);
            $vignette->setItemDifficulty($vignetteData['itemDifficulty']);
            $vignette->setRealitySimilarity($vignetteData['realitySimilarity']);
            $vignette->setSet($vignetteData['set']);
            $vignette->setSocialProximity($vignetteData['socialProximity']);

            $this->entityManager->persist($vignette);
        }

        $this->entityManager->flush();

        $io->success('Successfully seeded ' . count($vignettes) . ' vignettes!');

        return Command::SUCCESS;
    }
}
