import re
import datetime

from fiftystates.scrape import NoDataForPeriod
from fiftystates.scrape.events import EventScraper, Event

import lxml.html


def parse_datetime(s, year):
    dt = None

    match = re.match(r"[A-Z][a-z]{2,2} \d+, \d\d:\d\d (AM|PM)", s)
    if match:
        dt = datetime.datetime.strptime(match.group(0), "%b %d, %H:%M %p")

    match = re.match(r"[A-Z][a-z]{2,2} \d+", s)
    if match:
        dt = datetime.datetime.strptime(match.group(0), "%b %d").date()

    if dt:
        return dt.replace(year=int(year))
    else:
        raise ValueError("Bad date string: %s" % s)


class LAEventScraper(EventScraper):
    state = 'la'

    def scrape(self, chamber, session):
        if session != '2010':
            raise NoDataForPeriod(session)

        if chamber == 'lower':
            self.scrape_house_schedule(session)

    def scrape_house_schedule(self, session):
        url = "http://house.louisiana.gov/H_Sched/Hse_Sched_Weekly.htm"

        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            for link in page.xpath("//img[@alt = 'See Agenda in pdf']/.."):
                guid = link.attrib['href']

                committee = link.xpath("string(../../../td[1])").strip()

                when = link.xpath("string(../../../td[2])").strip()
                when = parse_datetime(when, session)

                description = 'Committee Meeting: %s' % committee

                event = Event(session, when, 'committee:meeting',
                              description)
                event.add_participant('committee', committee)
                event['link'] = guid

                self.save_event(event)
