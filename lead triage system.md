The problem is that there are multiple inbounds of leads coming in every month; for this use case, we have about 520 of them, and reviewing them manually is a lot of work. The solution is to design a system that automatically handles this and categorises them into three categories: Contact Now, Nurture, and Disqualified. Using an LLM to handle this would be somewhat inefficient and not worth it in this case. Looking at the notes left on each lead, we notice patterns that can help us determine who needs nurturing, who we can contact, and who is disqualified, paired with other things like budget and employee size.

The architecture is linear and direct: upload the CSV, then clean it. We need to clean it because the data comes in different forms — for example, the dates can come in as 06-05-2026, or as 5/6/2006 — so in order to properly score each lead, the data needs to be cleaned into a consistent format. The same goes for things like budget, which comes in as TBD, $8k, 12k/mo; all of this needs to be cleaned into a consistent format, so it becomes 8000, 12000 instead. After the cleaning is done, we score it, then rank it, and then show the user a CSV table of the cleaned, ranked data.

Two files: triage.py, which holds the logic, and app.py, the wrapper that holds the upload, display, and download — this calls the triage logic.

Hosted on Streamlit Cloud, deployed from GitHub.

The workflow is direct as explained: upload the CSV, you see the counts for Contact Now, Nurture, and Disqualified, with the ability to filter, and then you can download the original CSV but in its ranked form.

For the logic that determines who needs to be contacted, we start with eliminations first — hard disqualifiers — so non-buyers, either based on their notes or their title: students, journalists, investors, job seekers. We also check for spam rows and junk test rows.

There is also an intent score, and multiple things decide this. From the notes, you can tell who is ready to buy and who is still hesitating — that's the difference between Contact Now and Nurture. There's also budget stated vs. TBD and $0; they mean different things and are treated differently. TBD is not the same as $0, as TBD means it's undecided, but $0 means confirmed no money. And a stated budget means a ready customer.

There is also a fit score; the title, employee count, and budget floor play a role here. So people like CEO, Founder, Head of VPO, paired with the notes and budget, easily fall into Contact Now. We combine the two scores, resulting in a score out of 10, and based on the threshold we recommend — so 7+ is Contact Now, 3 to 6 is Nurture, and less than 3 is Disqualify.

I chose to just use pattern rules over an LLM in this case, as the notes are short and direct, self-explanatory, and the system works in a way like an actual user would skim through the file to decide. The only situation where a classifier would come in is if the notes get longer and messier in actual systems.

Originally I scored agency mentions as a fit signal, but changed my mind to use the title, as it's a much stronger field, because a lead being an agency doesn't mean they should automatically qualify or get an extra point — but for title, things like Owner, Founder, CEO, COO, these people can actually approve a purchase, and this is what matters regardless of company type.
